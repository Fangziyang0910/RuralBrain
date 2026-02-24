"""
Planning Service API 路由
提供规划咨询、知识库查询等端点
"""
import asyncio
import json
import logging
import time
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from src.rag.service.core.config import (
    SERVICE_NAME,
    SERVICE_VERSION,
    LOG_LEVEL,
)
from src.rag.service.schemas.chat import (
    PlanningChatRequest,
    DocumentListResponse,
    DocumentInfo,
    DocumentSummaryResponse,
    ChapterListResponse,
    ChapterInfo,
    HealthResponse,
    KnowledgeUpdateRequest,
    KnowledgeUpdateResponse,
)
from src.rag.core.context_manager import get_context_manager

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== 全局更新锁 ====================
_kb_update_lock = asyncio.Lock()


# ==================== 辅助函数 ====================

def extract_knowledge_sources(tool_output: str) -> list[dict]:
    """从工具输出中提取知识库来源信息"""
    import re

    sources = []
    pattern = r"【知识片段 \d+】\s*\n来源: ([^\n]+)\s*\n位置: 第(\d+)\s*(.*?)\s*\n内容:\s*([\s\S]*?)(?=【知识片段|$)"

    for match in re.findall(pattern, tool_output):
        source, page_num, doc_type, content = match
        content_preview = content.strip()[:300]
        if len(content_preview) == 300:
            content_preview += "..."

        sources.append({
            "source": source.strip(),
            "page": int(page_num),
            "doc_type": doc_type.strip() if doc_type else "",
            "content": content_preview,
        })

    return sources


# ==================== 延迟加载 Agent ====================

_agent_cache = None


def get_agent():
    """
    获取 Planning Agent（单例模式）

    Returns:
        配置好的 Agent 实例
    """
    global _agent_cache
    if _agent_cache is None:
        logger.info("正在创建 Planning Agent...")
        from src.agents.planning_agent import get_planning_agent

        _agent_cache = get_planning_agent()
        logger.info("Planning Agent 创建完成")

    return _agent_cache


# ==================== 核心端点 ====================

@router.get("/health", response_model=HealthResponse, tags=["系统"])
async def health_check():
    """健康检查端点"""
    try:
        from pathlib import Path
        from src.rag.config import CHROMA_PERSIST_DIR

        kb_loaded = Path(CHROMA_PERSIST_DIR).exists()

        return HealthResponse(
            status="healthy",
            service=SERVICE_NAME,
            version=SERVICE_VERSION,
            knowledge_base_loaded=kb_loaded,
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"服务不可用: {str(e)}"
        )


@router.post("/chat/planning", summary="规划咨询对话（流式）", tags=["规划咨询"])
async def planning_chat(request: PlanningChatRequest):
    """规划咨询对话接口（流式）"""
    request_id = str(uuid.uuid4())
    try:
        agent = get_agent()
        thread_id = request.thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        logger.info(f"[{request_id}] 收到规划咨询请求 [thread_id={thread_id}]: {request.message}")

        return StreamingResponse(
            _event_generator(agent, request, thread_id, config, request_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except Exception as e:
        logger.error(f"[{request_id}] 规划咨询请求失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"请求处理失败: {str(e)}"
        )


async def _event_generator(agent, request: PlanningChatRequest, thread_id: str, config: dict, request_id: str) -> AsyncGenerator[str, None]:
    """SSE 事件生成器"""
    tools_used = []
    full_content = ""
    knowledge_sources = []
    sources_sent = False
    start_time = time.time()
    tool_call_count = 0

    # 流式输出缓冲
    content_buffer = []
    BUFFER_SIZE = 1  # 逐字输出，避免卡顿感

    try:
        # 发送开始事件
        yield f"data: {json.dumps({'type': 'start', 'thread_id': thread_id, 'request_id': request_id}, ensure_ascii=False)}\n\n"

        input_data = {
            "messages": [HumanMessage(content=request.message)],
        }

        # 流式处理 agent 响应
        async for event in agent.astream_events(input_data, config, version="v2"):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    content_buffer.append(content)
                    # 当缓冲达到大小时发送
                    if len("".join(content_buffer)) >= BUFFER_SIZE:
                        buffered_content = "".join(content_buffer)
                        full_content += buffered_content
                        yield f"data: {json.dumps({'type': 'content', 'content': buffered_content}, ensure_ascii=False)}\n\n"
                        content_buffer = []

            elif kind == "on_tool_start":
                tool_name = event["name"]
                if tool_name not in tools_used:
                    tools_used.append(tool_name)
                tool_call_count += 1
                yield f"data: {json.dumps({'type': 'tool', 'tool_name': tool_name, 'status': 'started', 'tool_call_count': tool_call_count}, ensure_ascii=False)}\n\n"

            elif kind == "on_tool_end":
                tool_name = event["name"]
                tool_output = event["data"].get("output")
                output_str = str(tool_output.content) if hasattr(tool_output, "content") else str(tool_output)

                logger.info(f"[{request_id}] 工具 {tool_name} 输出预览: {output_str[:200]}...")

                # 提取知识库来源
                extracted_sources = extract_knowledge_sources(output_str)

                if tool_name == "search_knowledge":
                    logger.info(f"[{request_id}] [DEBUG] search_knowledge 输出长度: {len(output_str)}")
                    logger.info(f"[{request_id}] [DEBUG] 提取到 {len(extracted_sources)} 个来源")
                    if extracted_sources:
                        logger.info(f"[{request_id}] [DEBUG] 来源示例: {extracted_sources[0]}")

                if extracted_sources:
                    logger.info(f"[{request_id}] 提取到 {len(extracted_sources)} 个知识库来源")
                    knowledge_sources.extend(extracted_sources)

                yield f"data: {json.dumps({'type': 'tool', 'tool_name': tool_name, 'status': 'completed'}, ensure_ascii=False)}\n\n"

        # 发送知识库来源
        if knowledge_sources and not sources_sent:
            yield f"data: {json.dumps({'type': 'sources', 'sources': knowledge_sources}, ensure_ascii=False)}\n\n"
            sources_sent = True

        # 发送剩余的缓冲内容
        if content_buffer:
            buffered_content = "".join(content_buffer)
            full_content += buffered_content
            yield f"data: {json.dumps({'type': 'content', 'content': buffered_content}, ensure_ascii=False)}\n\n"

        # 发送结束事件
        total_time = time.time() - start_time
        end_data = {
            "type": "end",
            "thread_id": thread_id,
            "tools_used": tools_used,
            "tool_call_count": tool_call_count,
            "total_time": round(total_time, 2),
        }
        logger.info(f"[{request_id}] 请求完成 [thread_id={thread_id}, tools={len(tools_used)}, calls={tool_call_count}, time={total_time:.2f}s]")
        yield f"data: {json.dumps(end_data, ensure_ascii=False)}\n\n"

    except Exception as e:
        logger.error(f"[{request_id}] 流式响应生成错误: {e}")

        # 尝试发送已收集的知识库来源
        if knowledge_sources and not sources_sent:
            try:
                yield f"data: {json.dumps({'type': 'sources', 'sources': knowledge_sources}, ensure_ascii=False)}\n\n"
            except:
                pass

        yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"


# ==================== 知识库查询端点 ====================

@router.get("/knowledge/documents", response_model=DocumentListResponse, tags=["知识库"])
async def list_documents():
    """列出可用文档"""
    try:
        cm = get_context_manager()
        cm._ensure_loaded()

        documents = []
        total_chunks = 0

        for source, doc_idx in cm.doc_index.items():
            preview = doc_idx.chunks_info[0]["content_preview"] if doc_idx.chunks_info else ""
            doc_info = DocumentInfo(
                source=source,
                type=doc_idx.doc_type,
                chunk_count=len(doc_idx.chunks_info),
                preview=preview,
            )
            documents.append(doc_info)
            total_chunks += len(doc_idx.chunks_info)

        return DocumentListResponse(
            documents=documents,
            total_count=len(documents),
            total_chunks=total_chunks,
        )

    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档列表失败: {str(e)}"
        )


@router.get("/knowledge/summary/{source}", response_model=DocumentSummaryResponse, tags=["知识库"])
async def get_document_summary(source: str):
    """获取文档执行摘要"""
    try:
        cm = get_context_manager()
        result = cm.get_executive_summary(source)

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )

        return DocumentSummaryResponse(
            source=source,
            executive_summary=result.get("executive_summary") or "",
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档未找到: {source}"
        )
    except Exception as e:
        logger.error(f"获取文档摘要失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档摘要失败: {str(e)}"
        )


@router.get("/knowledge/chapters/{source}", response_model=ChapterListResponse, tags=["知识库"])
async def get_document_chapters(source: str):
    """列出文档章节摘要"""
    try:
        cm = get_context_manager()
        result = cm.list_chapter_summaries(source)

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )

        chapters = [
            ChapterInfo(
                header=ch["header"],
                summary=ch.get("summary", ""),
            )
            for ch in result.get("chapters", [])
        ]

        return ChapterListResponse(
            source=source,
            chapters=chapters,
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文档未找到: {source}"
        )
    except Exception as e:
        logger.error(f"获取章节列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取章节列表失败: {str(e)}"
        )


# ==================== 知识库更新端点 ====================

@router.post("/knowledge/update", response_model=KnowledgeUpdateResponse, tags=["知识库"])
async def update_knowledge_base(request: KnowledgeUpdateRequest, background_tasks=None):
    """
    更新知识库（线程安全）

    支持两种模式：
    - **增量更新**（默认）：仅处理新增/变更文档，保留现有数据
    - **全量重建**（force_rebuild=True）：清空后重新构建整个知识库

    数据源选项：
    - source: 单个文档路径
    - source_dir: 文档目录（批量处理）
    """
    # 使用全局锁确保更新操作串行执行
    async with _kb_update_lock:
        return await _update_knowledge_base_impl(request)


async def _update_knowledge_base_impl(request: KnowledgeUpdateRequest) -> KnowledgeUpdateResponse:
    """
    更新知识库的具体实现
    """
    import time
    from pathlib import Path

    start_time = time.time()

    try:
        from src.rag.config import CHROMA_PERSIST_DIR
        from src.rag.utils.loaders import (
            load_documents_from_directory,
            DOCLoader,
            DOCXLoader,
            PDFLoader,
            PPTXLoader,
            MarkdownLoader,
            TextFileLoader,
        )
        from langchain_chroma import Chroma
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from src.rag.config import get_embeddings_cached
        import hashlib

        # 1. 确定数据源
        source_files = []
        if request.source:
            source_path = Path(request.source)
            if not source_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"文件不存在: {request.source}"
                )
            source_files = [source_path]
            logger.info(f"单文件更新模式: {request.source}")

        elif request.source_dir:
            source_dir = Path(request.source_dir)
            if not source_dir.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"目录不存在: {request.source_dir}"
                )
            # 获取支持的文件
            supported_exts = [".md", ".txt", ".pptx", ".pdf", ".docx", ".doc"]
            source_files = [
                f for f in source_dir.rglob("*")
                if f.is_file() and f.suffix.lower() in supported_exts
            ]
            logger.info(f"目录更新模式: {request.source_dir} ({len(source_files)} 个文件)")

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="必须提供 source 或 source_dir 参数"
            )

        if not source_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未找到可处理的文档"
            )

        # 2. 全量重建模式
        if request.force_rebuild:
            logger.info("执行全量重建...")
            mode = "full"

            # 清空现有知识库
            chroma_dir = Path(CHROMA_PERSIST_DIR)
            if chroma_dir.exists():
                import shutil
                shutil.rmtree(chroma_dir)
                logger.info("已清空现有知识库")

            documents_removed = 0  # TODO: 可以从备份统计
        else:
            mode = "incremental"
            documents_removed = 0

        # 3. 加载文档
        all_documents = []
        for file_path in source_files:
            try:
                # 根据文件类型选择加载器
                ext = file_path.suffix.lower()
                if ext == ".pdf":
                    loader = PDFLoader(file_path, category=request.category)
                elif ext in [".doc", ".docx"]:
                    # 先尝试 DOCX，失败则用 DOC
                    try:
                        loader = DOCXLoader(file_path, category=request.category)
                        loader.load()
                    except:
                        loader = DOCLoader(file_path, category=request.category)
                elif ext == ".pptx":
                    loader = PPTXLoader(file_path, category=request.category)
                elif ext == ".md":
                    loader = MarkdownLoader(file_path, category=request.category)
                else:
                    loader = TextFileLoader(file_path, category=request.category)

                docs = loader.load()
                all_documents.extend(docs)
                logger.info(f"加载文档: {file_path.name} ({len(docs)} 个片段)")

            except Exception as e:
                logger.warning(f"跳过文件 {file_path.name}: {e}")
                continue

        if not all_documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未能加载任何有效文档"
            )

        # 4. 文本切分
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2500,
            chunk_overlap=500,
        )
        splits = text_splitter.split_documents(all_documents)
        logger.info(f"文本切分完成: {len(splits)} 个切片")

        # 5. 增量模式：去重
        documents_added = len(all_documents)
        chunks_added = len(splits)

        if mode == "incremental":
            # 检查已有文档，避免重复
            cm = get_context_manager()
            cm._ensure_loaded()

            existing_sources = set(cm.doc_index.keys())
            new_sources = set()

            for doc in all_documents:
                source = doc.metadata.get("source", "")
                if source and source not in existing_sources:
                    new_sources.add(source)

            # TODO: 实现更精细的切片去重
            logger.info(f"增量模式: {len(new_sources)} 个新文档")

        # 6. 向量化并存储
        logger.info("正在向量化并存储...")
        embeddings = get_embeddings_cached()

        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
        )

        # 清除缓存，确保新数据生效
        cm = get_context_manager()
        if hasattr(cm, '_loaded'):
            cm._loaded = False

        duration = time.time() - start_time

        logger.info(f"知识库更新完成: {documents_added} 文档, {chunks_added} 切片, 耗时 {duration:.2f}s")

        return KnowledgeUpdateResponse(
            success=True,
            mode=mode,
            documents_added=documents_added,
            chunks_added=chunks_added,
            documents_removed=documents_removed,
            message=f"成功更新知识库: {documents_added} 个文档, {chunks_added} 个切片",
            duration=round(duration, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"知识库更新失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"知识库更新失败: {str(e)}"
        )

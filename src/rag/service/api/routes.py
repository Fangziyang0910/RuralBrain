"""
Planning Service API 路由
提供规划咨询、知识库查询等端点
"""
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
)
from src.rag.core.context_manager import get_context_manager

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter()

# 模式指令
MODE_INSTRUCTIONS = {
    "fast": "⚡ 当前为快速模式：最多调用 2 次工具，优先使用 get_document_overview 和 search_key_points，避免使用 get_chapter_content 和 get_document_full。",
    "deep": "🔍 当前为深度模式：最多调用 5 次工具，可以使用所有工具包括 get_chapter_content 和 get_document_full 进行深度分析。",
    "auto": "🤖 当前为自动模式：根据问题复杂度自主选择工作模式和工具。",
}


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

_agent = None


def get_agent():
    """延迟加载 Planning Agent"""
    global _agent
    if _agent is None:
        logger.info("正在加载 Planning Agent...")
        from src.agents.planning_agent import agent as planning_agent
        _agent = planning_agent
        logger.info("Planning Agent 加载完成")
    return _agent


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
    try:
        agent = get_agent()
        thread_id = request.thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id, "mode": request.mode}}

        logger.info(f"收到规划咨询请求 [thread_id={thread_id}, mode={request.mode}]: {request.message}")

        return StreamingResponse(
            _event_generator(agent, request, thread_id, config),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    except Exception as e:
        logger.error(f"规划咨询请求失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"请求处理失败: {str(e)}"
        )


async def _event_generator(agent, request: PlanningChatRequest, thread_id: str, config: dict) -> AsyncGenerator[str, None]:
    """SSE 事件生成器"""
    tools_used = []
    full_content = ""
    knowledge_sources = []
    sources_sent = False
    start_time = time.time()
    tool_call_count = 0

    try:
        # 发送开始事件
        yield f"data: {json.dumps({'type': 'start', 'thread_id': thread_id, 'mode': request.mode}, ensure_ascii=False)}\n\n"

        # 构建增强消息
        mode_prefix = MODE_INSTRUCTIONS.get(request.mode, MODE_INSTRUCTIONS["auto"])
        enhanced_message = f"{mode_prefix}\n\n用户问题：{request.message}"

        input_data = {
            "messages": [HumanMessage(content=enhanced_message)],
            "mode": request.mode,
        }

        # 流式处理 agent 响应
        async for event in agent.astream_events(input_data, config, version="v2"):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    full_content += content
                    yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"

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

                logger.info(f"工具 {tool_name} 输出预览: {output_str[:200]}...")

                # 提取知识库来源
                extracted_sources = extract_knowledge_sources(output_str)

                if tool_name == "search_knowledge":
                    logger.info(f"[DEBUG] search_knowledge 输出长度: {len(output_str)}")
                    logger.info(f"[DEBUG] 提取到 {len(extracted_sources)} 个来源")
                    if extracted_sources:
                        logger.info(f"[DEBUG] 来源示例: {extracted_sources[0]}")

                if extracted_sources:
                    logger.info(f"提取到 {len(extracted_sources)} 个知识库来源")
                    knowledge_sources.extend(extracted_sources)

                yield f"data: {json.dumps({'type': 'tool', 'tool_name': tool_name, 'status': 'completed'}, ensure_ascii=False)}\n\n"

        # 发送知识库来源
        if knowledge_sources and not sources_sent:
            yield f"data: {json.dumps({'type': 'sources', 'sources': knowledge_sources}, ensure_ascii=False)}\n\n"
            sources_sent = True

        # 发送结束事件
        total_time = time.time() - start_time
        end_data = {
            "type": "end",
            "thread_id": thread_id,
            "tools_used": tools_used,
            "tool_call_count": tool_call_count,
            "total_time": round(total_time, 2),
            "mode": request.mode,
        }
        logger.info(f"请求完成 [thread_id={thread_id}, mode={request.mode}, tools={len(tools_used)}, calls={tool_call_count}, time={total_time:.2f}s]")
        yield f"data: {json.dumps(end_data, ensure_ascii=False)}\n\n"

    except Exception as e:
        logger.error(f"流式响应生成错误: {e}")

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

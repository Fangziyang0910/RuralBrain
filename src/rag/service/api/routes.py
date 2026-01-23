"""
Planning Service API 路由
提供规划咨询、知识库查询等端点
"""
import json
import logging
import uuid
from typing import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from langchain_core.messages import HumanMessage

# 导入配置和模型
from src.rag.service.core.config import (
    SERVICE_NAME,
    SERVICE_VERSION,
    API_PREFIX,
    LOG_LEVEL,
)
from src.rag.service.schemas.chat import (
    PlanningChatRequest,
    PlanningChatResponse,
    DocumentListResponse,
    DocumentInfo,
    DocumentSummaryResponse,
    ChapterListResponse,
    ChapterInfo,
    HealthResponse,
    ErrorResponse,
)

# 导入 RAG 核心组件
from src.rag.core.context_manager import get_context_manager
from src.rag.core.tools import (
    executive_summary_tool,
    chapter_summaries_list_tool,
    chapter_summary_tool,
    key_points_search_tool,
)

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


# ==================== 辅助函数 ====================

def _extract_knowledge_sources(tool_output: str) -> list[dict]:
    """
    从工具输出中提取知识库来源信息

    工具输出格式示例：
    【知识片段 1】
    来源: 罗浮-长宁山镇融合发展战略.pptx
    位置: 第3 pptx（或 第3页、第4docx）
    内容:
    ...

    Args:
        tool_output: 工具返回的文本

    Returns:
        来源信息列表，每个元素包含 source, page, content
    """
    import re

    sources = []

    # 使用正则表达式匹配知识片段
    # 匹配格式：【知识片段 X】来源: xxx位置: 第X [类型]内容:...
    # 优化：支持 "第X 类型"（有空格）和 "第X类型"（无空格）两种格式
    # 修复：改进 doc_type 提取，避免只提取部分字符（如 ptx 而不是 pptx）
    # 修复：移除内容后的 \n 要求，支持 "内容: xxx" 和 "内容:\nxxx" 两种格式
    pattern = r"【知识片段 \d+】\s*\n来源: ([^\n]+)\s*\n位置: 第(\d+)\s*(.*?)\s*\n内容:\s*([\s\S]*?)(?=【知识片段|$)"

    matches = re.findall(pattern, tool_output)

    for match in matches:
        source, page_num, doc_type, content = match

        # 清理 doc_type（去除前导空白）
        doc_type_clean = doc_type.strip() if doc_type else ""

        # 清理内容（取前300个字符作为预览）
        content_preview = content.strip()[:300]
        if len(content_preview) == 300:
            content_preview += "..."

        sources.append({
            "source": source.strip(),
            "page": int(page_num),
            "doc_type": doc_type_clean,
            "content": content_preview,
        })

    return sources

# ==================== 延迟加载 Planning Agent ====================
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
    """
    健康检查端点

    检查 Planning Service 的运行状态，包括：
    - 服务状态
    - 知识库加载状态
    - 模型可用性
    """
    try:
        # 检查知识库
        from src.rag.config import CHROMA_PERSIST_DIR
        from pathlib import Path

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


@router.post(
    "/chat/planning",
    summary="规划咨询对话（流式）",
    description="通过 Planning Agent 进行乡村规划咨询，支持流式响应",
    tags=["规划咨询"]
)
async def planning_chat(request: PlanningChatRequest):
    """
    # 规划咨询对话接口（流式）

    基于知识库提供乡村规划咨询服务，支持快速模式和深度模式。

    ## 工作模式
    - **auto**: AI 根据问题复杂度自动选择模式
    - **fast**: 快速浏览模式（使用摘要和要点）
    - **deep**: 深度分析模式（阅读完整文档）

    ## 响应格式
    使用 Server-Sent Events (SSE) 流式返回：
    - `start`: 会话开始
    - `content`: AI 回复内容（流式）
    - `tool`: 工具调用信息
    - `end`: 会话结束

    ## 示例
    ```bash
    curl -X POST "http://localhost:8003/api/v1/chat/planning" \
         -H "Content-Type: application/json" \
         -d '{"message": "长宁镇的旅游发展目标是什么？", "mode": "auto"}'
    ```
    """
    try:
        agent = get_agent()

        # 生成或使用线程ID
        thread_id = request.thread_id or str(uuid.uuid4())
        config = {
            "configurable": {
                "thread_id": thread_id,
                "mode": request.mode,  # 传递模式到 Agent 配置
            }
        }

        logger.info(
            f"收到规划咨询请求 [thread_id={thread_id}, mode={request.mode}]: {request.message}"
        )

        async def event_generator() -> AsyncGenerator[str, None]:
            """SSE 事件生成器"""
            tools_used = []
            full_content = ""
            knowledge_sources = []  # 收集所有知识库来源
            sources_sent = False  # 标记 sources 是否已发送

            # 添加性能统计
            import time
            start_time = time.time()
            tool_call_count = 0

            try:
                # 发送开始事件
                yield f"data: {json.dumps({'type': 'start', 'thread_id': thread_id, 'mode': request.mode}, ensure_ascii=False)}\n\n"

                # 模式指令前缀（让 Agent 在运行时感知当前模式）
                mode_instructions = {
                    "fast": "⚡ 当前为快速模式：最多调用 2 次工具，优先使用 get_document_overview 和 search_key_points，避免使用 get_chapter_content 和 get_document_full。",
                    "deep": "🔍 当前为深度模式：最多调用 5 次工具，可以使用所有工具包括 get_chapter_content 和 get_document_full 进行深度分析。",
                    "auto": "🤖 当前为自动模式：根据问题复杂度自主选择工作模式和工具。"
                }

                # 构建带有模式指令的消息
                mode_prefix = mode_instructions.get(request.mode, mode_instructions["auto"])
                enhanced_message = f"{mode_prefix}\n\n用户问题：{request.message}"

                # 准备输入数据（包含模式）
                input_data = {
                    "messages": [HumanMessage(content=enhanced_message)],
                    "mode": request.mode,  # 传递模式到输入状态
                }

                # 流式处理 agent 响应
                async for event in agent.astream_events(
                    input_data,
                    config,
                    version="v2",
                ):
                    kind = event["event"]

                    # 处理流式消息内容
                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content:
                            full_content += content
                            event_data = {
                                "type": "content",
                                "content": content,
                            }
                            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                    # 处理工具调用
                    elif kind == "on_tool_start":
                        tool_name = event["name"]
                        if tool_name not in tools_used:
                            tools_used.append(tool_name)
                        tool_call_count += 1  # 统计工具调用次数
                        event_data = {
                            "type": "tool",
                            "tool_name": tool_name,
                            "status": "started",
                            "tool_call_count": tool_call_count,  # 添加调用计数
                        }
                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                    elif kind == "on_tool_end":
                        tool_name = event["name"]
                        tool_output = event["data"].get("output")

                        # 将 ToolMessage 对象转换为字符串
                        output_str = str(tool_output.content) if hasattr(tool_output, "content") else str(tool_output)

                        # 调试：记录工具输出（只记录前200字符）
                        logger.info(f"工具 {tool_name} 输出预览: {output_str[:200]}...")

                        # 从工具输出中提取知识库来源
                        extracted_sources = _extract_knowledge_sources(output_str)

                        # 调试：记录提取结果
                        if tool_name == "search_knowledge":
                            logger.info(f"[DEBUG] search_knowledge 输出长度: {len(output_str)}")
                            logger.info(f"[DEBUG] 提取到 {len(extracted_sources)} 个来源")
                            if extracted_sources:
                                logger.info(f"[DEBUG] 来源示例: {extracted_sources[0]}")

                        if extracted_sources:
                            logger.info(f"提取到 {len(extracted_sources)} 个知识库来源")
                            knowledge_sources.extend(extracted_sources)

                        event_data = {
                            "type": "tool",
                            "tool_name": tool_name,
                            "status": "completed",
                        }
                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                # 发送知识库来源（在正常流程结束时）
                if knowledge_sources and not sources_sent:
                    sources_data = {
                        "type": "sources",
                        "sources": knowledge_sources,
                    }
                    yield f"data: {json.dumps(sources_data, ensure_ascii=False)}\n\n"
                    sources_sent = True

                # 计算总耗时
                total_time = time.time() - start_time

                # 发送结束事件（包含性能统计）
                end_data = {
                    "type": "end",
                    "thread_id": thread_id,
                    "tools_used": tools_used,
                    "tool_call_count": tool_call_count,  # 工具调用总次数
                    "total_time": round(total_time, 2),  # 总耗时（秒）
                    "mode": request.mode,
                }
                logger.info(
                    f"请求完成 [thread_id={thread_id}, mode={request.mode}, "
                    f"tools={len(tools_used)}, calls={tool_call_count}, time={total_time:.2f}s]"
                )
                yield f"data: {json.dumps(end_data, ensure_ascii=False)}\n\n"

            except Exception as e:
                logger.error(f"流式响应生成错误: {e}")

                # 在错误发生前尝试发送已收集的知识库来源
                if knowledge_sources and not sources_sent:
                    sources_data = {
                        "type": "sources",
                        "sources": knowledge_sources,
                    }
                    try:
                        yield f"data: {json.dumps(sources_data, ensure_ascii=False)}\n\n"
                    except:
                        pass  # 如果发送失败，忽略

                error_data = {
                    "type": "error",
                    "error": str(e),
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
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


# ==================== 知识库查询端点 ====================

@router.get(
    "/knowledge/documents",
    response_model=DocumentListResponse,
    summary="列出可用文档",
    description="获取知识库中所有可用的文档列表",
    tags=["知识库"]
)
async def list_documents():
    """
    # 列出可用文档

    返回知识库中所有文档的信息，包括：
    - 文档名称
    - 文档类型（政策/案例）
    - 切片数量
    - 内容预览
    """
    try:
        # 直接使用 ContextManager 获取文档列表
        cm = get_context_manager()
        cm._ensure_loaded()

        documents = []
        total_chunks = 0

        for source, doc_idx in cm.doc_index.items():
            doc_info = DocumentInfo(
                source=source,
                type=doc_idx.doc_type,
                chunk_count=len(doc_idx.chunks_info),
                preview=doc_idx.chunks_info[0]["content_preview"] if doc_idx.chunks_info else "",
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


@router.get(
    "/knowledge/summary/{source}",
    response_model=DocumentSummaryResponse,
    summary="获取文档执行摘要",
    description="获取指定文档的200字执行摘要",
    tags=["知识库"]
)
async def get_document_summary(source: str):
    """
    # 获取文档执行摘要

    返回文档的执行摘要，包含：
    - 核心目标
    - 定位
    - 关键指标
    - 重点措施

    ## 参数
    - **source**: 文档文件名（需要进行 URL 编码）

    ## 示例
    ```bash
    curl "http://localhost:8003/api/v1/knowledge/summary/罗浮-长宁山镇融合发展战略.pptx"
    ```
    """
    try:
        # 直接使用 ContextManager
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


@router.get(
    "/knowledge/chapters/{source}",
    response_model=ChapterListResponse,
    summary="列出文档章节摘要",
    description="获取指定文档的所有章节及其摘要",
    tags=["知识库"]
)
async def get_document_chapters(source: str):
    """
    # 列出文档章节摘要

    返回文档的所有章节信息，包括：
    - 章节标题
    - 章节摘要

    ## 参数
    - **source**: 文档文件名（需要进行 URL 编码）

    ## 示例
    ```bash
    curl "http://localhost:8003/api/v1/knowledge/chapters/罗浮-长宁山镇融合发展战略.pptx"
    ```
    """
    try:
        # 直接使用 ContextManager
        cm = get_context_manager()
        result = cm.list_chapter_summaries(source)

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )

        chapters = []
        for ch in result.get("chapters", []):
            chapter_info = ChapterInfo(
                header=ch["header"],
                summary=ch.get("summary", ""),
            )
            chapters.append(chapter_info)

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


# ==================== 错误处理 ====================
# 注意：全局异常处理在 FastAPI 应用层（main.py）配置，不在路由层配置

"""
RuralBrain FastAPI 服务器
提供图像检测对话接口和规划咨询接口
"""
import sys
import json
import os
import uuid
import logging
from pathlib import Path
from typing import AsyncGenerator

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

from service.settings import (
    ALLOWED_ORIGINS,
    UPLOAD_DIR,
    MAX_UPLOAD_SIZE,
    ALLOWED_EXTENSIONS,
)
from service.schemas import ChatRequest, UploadResponse
from src.agents.middleware.dynamic_tool_middleware import set_kb_switch_state
from src.rag.service.schemas.chat import KnowledgeUpdateRequest, KnowledgeUpdateResponse
from src.rag.service.api.routes import _update_knowledge_base_impl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SSE 响应头常量
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
}


# ==================== 推理过程过滤器 ====================

class ThinkingProcessFilter:
    """
    过滤 Agent 推理过程的冗余输出

    限制"让我..."类推理句子的数量，减少前端显示的冗余信息。
    """
    # 匹配"让我..."类句子的正则模式
    THINKING_PATTERNS = [
        r"^(让我|现在让我|接下来让我|首先让我)",
        r"^(我来帮您|我来)",
        r"^(很好！|很好，|好的，)",
        r"^(让我先|让我先查看|让我先尝试)",
    ]

    # 最多允许的推理句子数量
    MAX_THINKING_SENTENCES = 2

    def __init__(self):
        self.thinking_sentence_count = 0
        self.current_sentence = ""
        self.sentence_buffer = ""
        self.in_final_answer = False

    def process(self, content: str) -> tuple[str, bool]:
        """
        处理流式内容，返回（过滤后的内容，是否应发送）

        Args:
            content: 流式输入的字符片段

        Returns:
            (过滤后的内容, 是否应该发送到前端)
        """
        if self.in_final_answer:
            # 已进入最终回答阶段，直接输出
            return content, True

        self.current_sentence += content

        # 检查是否到达句子边界
        if self._is_sentence_boundary(self.current_sentence[-1:]):
            sentence = self.current_sentence
            self.current_sentence = ""

            # 检查是否是推理句子
            if self._is_thinking_sentence(sentence):
                self.thinking_sentence_count += 1

                # 超过阈值，过滤掉
                if self.thinking_sentence_count > self.MAX_THINKING_SENTENCES:
                    logger.info(f"过滤推理句子 (已超过 {self.MAX_THINKING_SENTENCES} 句): {sentence[:50]}...")
                    return "", False

            # 添加到缓冲
            self.sentence_buffer += sentence

            # 返回完整句子
            return sentence, True

        # 未到句子边界，返回空（继续累积）
        return "", False

    def mark_final_answer(self):
        """标记进入最终回答阶段"""
        self.in_final_answer = True
        # 清空当前累积的内容
        if self.current_sentence:
            remaining = self.current_sentence
            self.current_sentence = ""
            return remaining
        return ""

    def _is_sentence_boundary(self, char: str) -> bool:
        """检查字符是否是句子边界"""
        return char in "。！？\n"

    def _is_thinking_sentence(self, sentence: str) -> bool:
        """检查句子是否是推理过程句子"""
        import re
        sentence = sentence.strip()
        for pattern in self.THINKING_PATTERNS:
            # 使用 search 而不是 match，以匹配任何位置
            if re.search(pattern, sentence):
                return True
        return False

app = FastAPI(
    title="RuralBrain API",
    description="乡村智慧大脑 - 图像检测对话服务",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def mount_static_dirs():
    """挂载所有静态文件目录"""
    from service.settings import DETECTION_RESULTS_DIR

    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

    # 挂载检测结果目录
    for detection_type in ["pest", "cow", "rice"]:
        url_path = f"/{detection_type}_results"
        dir_path = DETECTION_RESULTS_DIR / detection_type
        if dir_path.exists():
            app.mount(url_path, StaticFiles(directory=str(dir_path)), name=detection_type)


mount_static_dirs()

# --------延迟加载机制--------
# 延迟导入 agent，避免启动时加载模型，缩短启动时间
_agent = None
_agent_version = None


def get_agent():
    """延迟加载统一编排 Agent（V2 Skills 架构）"""
    global _agent, _agent_version

    if _agent is None:
        from src.agents.orchestrator_agent_v2 import agent
        _agent = agent
        _agent_version = "orchestrator_v2"
        logger.info("✓ 统一编排 Agent V2 加载完成 - Skills 架构")

    return _agent


def get_agent_version() -> str:
    """
    获取当前使用的 Agent 版本

    Returns:
        "orchestrator" 或其他版本标识
    """
    global _agent_version
    if _agent_version is None:
        # 如果 Agent 还未加载，返回默认版本
        return "orchestrator"
    return _agent_version


@app.on_event("startup")
async def startup_event():
    """启动时预加载模型"""
    logger.info("RuralBrain 服务启动中...")
    logger.info("Agent 配置: Orchestrator Agent (统一编排)")

    get_agent()  # 预加载 Orchestrator Agent

    logger.info("RuralBrain 服务启动完成")


# -------- 意图识别函数 --------
def classify_intent(message: str, has_images: bool = False) -> str:
    """
    分类用户意图

    Args:
        message: 用户消息
        has_images: 是否包含图片

    Returns:
        意图类型: detection/general
    """
    # 规则1: 如果有图片，优先检测
    if has_images:
        return "detection"

    # 规则2: 检测相关关键词
    detection_keywords = [
        "识别", "检测", "害虫", "病害", "大米", "品种", "牛", "奶牛",
        "图片", "照片", "看", "什么", "分析", "诊断", "分类"
    ]

    message_lower = message.lower()

    # 统计关键词匹配
    detection_matches = sum(1 for kw in detection_keywords if kw in message)

    # 如果检测相关关键词较多，返回 detection
    if detection_matches >= 2:
        return "detection"

    # 默认为通用对话（Agent 会根据内容自主决定是否调用规划 skill）
    return "general"


# -------- API 路由定义--------
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "RuralBrain API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/upload", response_model=UploadResponse)
async def upload_image(files: list[UploadFile] = File(...)):
    """
    上传图片接口（支持单张或多张）
    
    Args:
        files: 上传的图片文件列表（最多10张）
        
    Returns:
        上传响应，包含文件路径列表
    """
    # 限制上传图片数量
    MAX_FILES = 10
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"一次最多上传 {MAX_FILES} 张图片",
        )
    
    try:
        file_paths = []
        
        for file in files:
            # 检查文件大小
            contents = await file.read()
            if len(contents) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"文件 {file.filename} 大小超过限制 ({MAX_UPLOAD_SIZE / 1024 / 1024}MB)",
                )
            
            # 检查文件扩展名
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"文件 {file.filename} 格式不支持，仅支持: {', '.join(ALLOWED_EXTENSIONS)}",
                )
            
            # 生成唯一文件名
            filename = f"{uuid.uuid4()}{file_ext}"
            file_path = UPLOAD_DIR / filename
            
            # 保存文件
            with open(file_path, "wb") as f:
                f.write(contents)
            
            file_paths.append(str(file_path))
            logger.info(f"文件上传成功: {filename}")
        
        # 兼容旧版本：如果只有一张图片，同时返回 file_path
        return UploadResponse(
            success=True,
            file_path=file_paths[0] if len(file_paths) == 1 else None,
            file_paths=file_paths,
            message=f"成功上传 {len(file_paths)} 张图片",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败: {str(e)}",
        )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    统一流式对话接口，使用 Orchestrator Agent 智能路由

    Orchestrator Agent 会自动判断用户意图：
    - 有图片 → 调用图像检测
    - 规划相关问题 → 调用规划知识库（规划 skill）
    - 支持多步推理和场景切换

    Args:
        request: 聊天请求，包含消息和可选的图片路径

    Returns:
        SSE 流式响应
    """
    try:
        # 生成或使用线程ID
        thread_id = request.thread_id or str(uuid.uuid4())

        # 支持多图片路径（新版本）或单图片路径（兼容旧版本）
        image_paths = request.image_paths or ([request.image_path] if request.image_path else [])

        # 获取 Orchestrator Agent
        agent = get_agent()
        config = {
            "configurable": {
                "thread_id": thread_id,
                "enable_knowledge_base": request.enable_knowledge_base,
            },
            "recursion_limit": 50,  # 防止递归限制
        }

        # 构建消息内容
        message_content = request.message

        if image_paths:
            # 如果有图片，在消息中包含所有图片路径
            paths_text = "\n".join([f"[图片路径 {i+1}: {path}]" for i, path in enumerate(image_paths)])
            message_content = f"{message_content}\n\n{paths_text}"

        logger.info(f"调用 Orchestrator Agent [thread_id={thread_id}]: {request.message[:50]}..., 图片数量: {len(image_paths)}, 知识库: {request.enable_knowledge_base}")
        # 调试：打印完整的消息内容
        logger.info(f"发送给 Agent 的消息内容: {message_content[:500]}...")

        # 保存知识库开关状态到中间件（供 load_skill 工具使用）
        logger.info(f"准备设置知识库开关: thread_id={thread_id}, enable_knowledge_base={request.enable_knowledge_base}")
        if request.enable_knowledge_base is not None:
            set_kb_switch_state(thread_id, request.enable_knowledge_base)
            logger.info(f"设置知识库开关: thread_id={thread_id}, enabled={request.enable_knowledge_base}")
        else:
            logger.info(f"知识库开关未设置 (None)，跳过状态设置")

        async def event_generator() -> AsyncGenerator[str, None]:
            """SSE 事件生成器"""
            try:
                # 发送开始事件
                yield f"data: {json.dumps({'type': 'start', 'thread_id': thread_id}, ensure_ascii=False)}\n\n"

                # 初始化推理过程过滤器
                thinking_filter = ThinkingProcessFilter()

                # 流式处理 agent 响应
                full_content = ""
                content_buffer = []
                BUFFER_SIZE = 1  # 逐字输出，避免卡顿感

                async for event in agent.astream_events(
                    {"messages": [HumanMessage(content=message_content)]},
                    config,
                    version="v2",
                ):
                    kind = event["event"]

                    # 处理流式消息内容（AI 的回答）
                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content:
                            # 应用推理过程过滤器
                            filtered_content, should_send = thinking_filter.process(content)

                            if should_send and filtered_content:
                                content_buffer.append(filtered_content)
                                # 当缓冲达到大小时发送
                                if len("".join(content_buffer)) >= BUFFER_SIZE:
                                    buffered_content = "".join(content_buffer)
                                    full_content += buffered_content
                                    event_data = {
                                        "type": "content",
                                        "content": buffered_content,
                                    }
                                    yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                                    content_buffer = []

                    # 处理工具调用结束事件
                    elif kind == "on_tool_end":
                        tool_name = event["name"]
                        logger.info(f"工具调用完成: {tool_name}")

                        # 查找对应的结果图片路径（仅检测工具）
                        result_image = None
                        if tool_name == "pest_detection_tool":
                            # 查找最新的害虫检测结果图片
                            from service.settings import DETECTION_RESULTS_DIR
                            result_dir = DETECTION_RESULTS_DIR / "pest"
                            if result_dir.exists():
                                images = sorted(result_dir.glob("pest_detection_result_*.jpg"),
                                              key=lambda p: p.stat().st_mtime, reverse=True)
                                if images:
                                    result_image = f"/pest_results/{images[0].name}"

                        elif tool_name == "rice_detection_tool":
                            # 查找最新的大米检测结果图片
                            from service.settings import DETECTION_RESULTS_DIR
                            result_dir = DETECTION_RESULTS_DIR / "rice"
                            if result_dir.exists():
                                images = sorted(result_dir.glob("rice_detection_result_*.jpg"),
                                              key=lambda p: p.stat().st_mtime, reverse=True)
                                if images:
                                    result_image = f"/rice_results/{images[0].name}"

                        elif tool_name == "cow_detection_tool":
                            # 查找最新的牛只检测结果图片
                            from service.settings import DETECTION_RESULTS_DIR
                            result_dir = DETECTION_RESULTS_DIR / "cow"
                            if result_dir.exists():
                                images = sorted(result_dir.glob("cow_detection_result_*.jpg"),
                                              key=lambda p: p.stat().st_mtime, reverse=True)
                                if images:
                                    result_image = f"/cow_results/{images[0].name}"

                        # 发送工具调用完成事件
                        # 添加完整的基础 URL（前端通过前端 API 路由访问）
                        tool_event = {
                            "type": "tool_call",
                            "tool_name": tool_name,
                            "status": "已完成",
                            "result_image": result_image,  # 相对路径，前端会通过代理访问
                        }
                        yield f"data: {json.dumps(tool_event, ensure_ascii=False)}\n\n"

                # 发送剩余的缓冲内容
                if content_buffer:
                    buffered_content = "".join(content_buffer)
                    full_content += buffered_content
                    event_data = {
                        "type": "content",
                        "content": buffered_content,
                    }
                    yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

                # 发送完成事件
                yield f"data: {json.dumps({'type': 'end', 'full_content': full_content}, ensure_ascii=False)}\n\n"

                logger.info(f"对话完成 [thread_id={thread_id}]")

            except Exception as e:
                logger.error(f"对话处理错误: {str(e)}")
                error_data = {
                    "type": "error",
                    "error": str(e),
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        # 使用 StreamingResponse 包装生成器
        return StreamingResponse(
            event_generator(),
            # 设置 SSE 媒体类型
            media_type="text/event-stream",
            # 禁用缓存，防止代理服务器缓冲响应，确保实时性
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        logger.error(f"对话请求失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ==================== 知识库更新 API ====================

@app.post("/api/v1/knowledge/update", response_model=KnowledgeUpdateResponse, tags=["知识库"])
async def update_knowledge_base(request: KnowledgeUpdateRequest):
    """
    更新知识库（线程安全）

    支持两种模式：
    - **增量更新**（默认）：仅处理新增/变更文档，保留现有数据
    - **全量重建**（force_rebuild=True）：清空后重新构建整个知识库

    数据源选项：
    - source: 单个文档路径
    - source_dir: 文档目录（批量处理）
    """
    return await _update_knowledge_base_impl(request)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理"""
    logger.error(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "服务器内部错误"},
    )


if __name__ == "__main__":
    import uvicorn
    from service.settings import HOST, PORT
    
    uvicorn.run(
        "service.server:app",
        host=HOST,
        port=PORT,
        reload=True,
    )

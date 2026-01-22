"""
RuralBrain FastAPI 服务器
提供图像检测对话接口和规划咨询接口
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径，确保可以直接运行此文件
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import json
import uuid
import logging
from typing import AsyncGenerator
from datetime import datetime

# 加载环境变量（必须在所有其他导入之前）
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage, AIMessageChunk
import httpx

from service.settings import (
    ALLOWED_ORIGINS,
    UPLOAD_DIR,
    MAX_UPLOAD_SIZE,
    ALLOWED_EXTENSIONS,
    AGENT_VERSION,
    AGENT_AUTO_FALLBACK,
)
from service.schemas import ChatRequest, UploadResponse, ErrorResponse

# --------应用初始化--------
# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用实例
app = FastAPI(
    title="RuralBrain API",
    description="乡村智慧大脑 - 图像检测对话服务",
    version="0.1.0",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------挂载静态文件目录--------
# 将服务器本地的文件目录映射为可通过 HTTP 访问的静态资源路径
# 挂载上传文件目录
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# 挂载害虫检测结果目录
pest_results_dir = Path("pest_detection_results")
pest_results_dir.mkdir(exist_ok=True)
app.mount("/pest_results", StaticFiles(directory=str(pest_results_dir)), name="pest_results")

# 挂载牛只检测结果目录
cow_results_dir = Path("cow_detection_results")
cow_results_dir.mkdir(exist_ok=True)
app.mount("/cow_results", StaticFiles(directory=str(cow_results_dir)), name="cow_results")

# 挂载大米检测结果目录
rice_results_dir = Path("rice_detection_results")
rice_results_dir.mkdir(parents=True, exist_ok=True)
app.mount("/rice_results", StaticFiles(directory=str(rice_results_dir)), name="rice_results")

# --------延迟加载机制--------
# 延迟导入 agent，避免启动时加载模型，缩短启动时间
_agent = None
_agent_version = None


def get_agent():
    """
    延迟加载 image_detection_agent
    支持版本切换：通过 AGENT_VERSION 环境变量选择 v1 或 v2
    """
    global _agent, _agent_version

    if _agent is None:
        logger.info(f"正在加载 AI 模型 [配置版本: {AGENT_VERSION}]...")

        try:
            # 尝试加载配置的版本
            if AGENT_VERSION == "v2":
                logger.info("→ 尝试加载 V2 Agent (Skills 架构)...")
                from src.agents.image_detection_agent_v2 import agent as agent_v2
                _agent = agent_v2
                _agent_version = "v2"
                logger.info("✓ V2 Agent (Skills 架构) 加载完成")
            else:  # v1 或其他
                logger.info("→ 加载 V1 Agent (传统架构)...")
                from src.agents.image_detection_agent import agent as agent_v1
                _agent = agent_v1
                _agent_version = "v1"
                logger.info("✓ V1 Agent (传统架构) 加载完成")

        except Exception as e:
            # V2 加载失败时的降级处理
            if AGENT_VERSION == "v2" and AGENT_AUTO_FALLBACK:
                logger.warning(f"⚠ V2 Agent 加载失败: {e}")
                logger.info("→ 自动回退到 V1 Agent...")
                try:
                    from src.agents.image_detection_agent import agent as agent_v1
                    _agent = agent_v1
                    _agent_version = "v1"
                    logger.info("✓ V1 Agent (回退) 加载完成")
                except Exception as fallback_error:
                    logger.error(f"✗ V1 Agent 回退也失败: {fallback_error}")
                    raise
            else:
                logger.error(f"✗ Agent 加载失败: {e}")
                raise

    return _agent


def get_agent_version() -> str:
    """
    获取当前使用的 Agent 版本

    Returns:
        "v1" 或 "v2"
    """
    global _agent_version
    if _agent_version is None:
        # 如果 Agent 还未加载，返回配置的版本
        return AGENT_VERSION
    return _agent_version


@app.on_event("startup")
async def startup_event():
    """启动时预加载模型"""
    logger.info("RuralBrain 服务启动中...")
    logger.info(f"Agent 配置版本: {AGENT_VERSION.upper()}")

    get_agent()  # 预加载模型

    # 显示实际使用的版本
    actual_version = get_agent_version()
    logger.info(f"Agent 实际版本: {actual_version.upper()}")
    logger.info("RuralBrain 服务启动完成")


# -------- Planning Service 配置 --------
PLANNING_SERVICE_URL = os.getenv(
    "PLANNING_SERVICE_URL",
    "http://localhost:8003"
)
PLANNING_SERVICE_TIMEOUT = int(os.getenv("PLANNING_SERVICE_TIMEOUT", "120"))


# -------- 意图识别函数 --------
def classify_intent(message: str, has_images: bool = False) -> str:
    """
    分类用户意图

    Args:
        message: 用户消息
        has_images: 是否包含图片

    Returns:
        意图类型: detection/planning
    """
    # 规则1: 如果有图片，优先检测
    if has_images:
        return "detection"

    # 规则2: 规划相关关键词
    planning_keywords = [
        "规划", "发展", "策略", "旅游", "产业", "博罗", "罗浮山", "长宁镇",
        "古城", "政策", "方案", "乡村", "振兴", "农业", "民宿", "文化",
        "设计", "建设", "布局", "目标", "措施", "项目", "投资", "招商"
    ]

    # 规则3: 检测相关关键词
    detection_keywords = [
        "识别", "检测", "害虫", "病害", "大米", "品种", "牛", "奶牛",
        "图片", "照片", "看", "什么", "分析", "诊断", "分类"
    ]

    message_lower = message.lower()

    # 统计关键词匹配
    planning_matches = sum(1 for kw in planning_keywords if kw in message)
    detection_matches = sum(1 for kw in detection_keywords if kw in message)

    # 根据匹配数量判断
    if planning_matches > detection_matches:
        return "planning"
    elif detection_matches > planning_matches:
        return "detection"
    elif planning_matches > 0:
        return "planning"
    else:
        # 默认为规划咨询
        return "planning"


async def forward_to_planning_service(
    message: str,
    thread_id: str = None,
    mode: str = "auto"
) -> AsyncGenerator[str, None]:
    """
    转发请求到 Planning Service

    Args:
        message: 用户消息
        thread_id: 对话线程ID
        mode: 工作模式

    Yields:
        SSE 事件数据
    """
    url = f"{PLANNING_SERVICE_URL}/api/v1/chat/planning"
    request_data = {
        "message": message,
        "mode": mode,
    }
    if thread_id:
        request_data["thread_id"] = thread_id

    try:
        async with httpx.AsyncClient(timeout=PLANNING_SERVICE_TIMEOUT) as client:
            async with client.stream("POST", url, json=request_data) as response:
                if response.status_code != 200:
                    error_data = {
                        "type": "error",
                        "error": f"Planning Service 返回错误: {response.status_code}",
                    }
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                    return

                # 流式转发响应
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        # 直接转发 SSE 事件
                        yield f"{line}\n"

    except httpx.ConnectError:
        error_data = {
            "type": "error",
            "error": "无法连接到 Planning Service，请确认服务已启动",
        }
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    except httpx.TimeoutException:
        error_data = {
            "type": "error",
            "error": f"Planning Service 响应超时（{PLANNING_SERVICE_TIMEOUT}秒）",
        }
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    except Exception as e:
        error_data = {
            "type": "error",
            "error": f"Planning Service 通信错误: {str(e)}",
        }
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"


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


@app.post("/chat/planning")
async def chat_planning(request: ChatRequest):
    """
    规划咨询对话接口（代理到 Planning Service）

    Args:
        request: 聊天请求

    Returns:
        SSE 流式响应
    """
    try:
        # 生成或使用线程ID
        thread_id = request.thread_id or str(uuid.uuid4())
        mode = request.mode or "auto"

        logger.info(f"收到规划咨询请求 [thread_id={thread_id}, mode={mode}]: {request.message}")

        async def event_generator() -> AsyncGenerator[str, None]:
            """SSE 事件生成器"""
            async for event in forward_to_planning_service(
                message=request.message,
                thread_id=thread_id,
                mode=mode
            ):
                yield event

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        logger.error(f"规划咨询请求失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    统一流式对话接口，根据 mode 参数路由到不同的服务

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

        # 判断调用哪个服务
        request_mode = request.mode or "auto"

        # 意图识别
        if request_mode == "auto":
            intent = classify_intent(request.message, len(image_paths) > 0)
            logger.info(f"意图识别结果: {intent}, 图片数量: {len(image_paths)}")
        else:
            intent = request_mode
            logger.info(f"指定模式: {intent}")

        # 如果是规划咨询模式且没有图片，转发到 Planning Service
        if intent == "planning" and len(image_paths) == 0:
            logger.info(f"转发到 Planning Service [thread_id={thread_id}, work_mode={request.work_mode}]: {request.message}")

            async def event_generator() -> AsyncGenerator[str, None]:
                async for event in forward_to_planning_service(
                    message=request.message,
                    thread_id=thread_id,
                    mode=request.work_mode or "auto"
                ):
                    yield event

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )

        # 否则使用图像检测 Agent
        agent = get_agent()
        config = {"configurable": {"thread_id": thread_id}}

        # 构建消息内容
        message_content = request.message

        if image_paths:
            # 如果有图片，在消息中包含所有图片路径
            paths_text = "\n".join([f"[图片路径 {i+1}: {path}]" for i, path in enumerate(image_paths)])
            message_content = f"{request.message}\n\n{paths_text}"

        agent_version = get_agent_version()
        logger.info(f"调用图像检测 Agent [版本: {agent_version.upper()}, thread_id={thread_id}]: {request.message}, 图片数量: {len(image_paths)}")
        
        async def event_generator() -> AsyncGenerator[str, None]:
            """SSE 事件生成器"""
            try:
                # 发送开始事件
                yield f"data: {json.dumps({'type': 'start', 'thread_id': thread_id}, ensure_ascii=False)}\n\n"
                
                # 流式处理 agent 响应
                full_content = ""
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
                            full_content += content
                            event_data = {
                                "type": "content",
                                "content": content,
                            }
                            yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                    
                    # 处理工具调用结束事件
                    elif kind == "on_tool_end":
                        tool_name = event["name"]
                        
                        # 查找对应的结果图片路径
                        result_image = None
                        if tool_name == "pest_detection_tool":
                            # 查找最新的害虫检测结果图片
                            result_dir = Path("pest_detection_results")
                            if result_dir.exists():
                                images = sorted(result_dir.glob("pest_detection_*.jpg"), 
                                              key=lambda p: p.stat().st_mtime, reverse=True)
                                if images:
                                    result_image = f"/pest_results/{images[0].name}"
                        
                        elif tool_name == "rice_detection_tool":
                            # 查找最新的大米检测结果图片
                            result_dir = Path("rice_detection_results")
                            if result_dir.exists():
                                images = sorted(result_dir.glob("rice_detection_*.jpg"), 
                                              key=lambda p: p.stat().st_mtime, reverse=True)
                                if images:
                                    result_image = f"/rice_results/{images[0].name}"
                        
                        elif tool_name == "cow_detection_tool":
                            # 查找最新的牛只检测结果图片
                            result_dir = Path("cow_detection_results")
                            if result_dir.exists():
                                images = sorted(result_dir.glob("cow_result_*.jpg"), 
                                              key=lambda p: p.stat().st_mtime, reverse=True)
                                if images:
                                    result_image = f"/cow_results/{images[0].name}"
                        
                        # 发送工具调用完成事件
                        tool_event = {
                            "type": "tool_call",
                            "tool_name": tool_name,
                            "status": "已完成",
                            "result_image": result_image,
                        }
                        yield f"data: {json.dumps(tool_event, ensure_ascii=False)}\n\n"
                
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

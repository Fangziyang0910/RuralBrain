"""
RuralBrain FastAPI 服务器
提供图像检测对话接口
"""
import os
import json
import uuid
import logging
from pathlib import Path
from typing import AsyncGenerator
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from langchain_core.messages import HumanMessage, AIMessageChunk

from service.settings import (
    ALLOWED_ORIGINS,
    UPLOAD_DIR,
    MAX_UPLOAD_SIZE,
    ALLOWED_EXTENSIONS,
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

# --------延迟加载机制--------
# 延迟导入 agent，避免启动时加载模型，缩短启动时间
_agent = None


def get_agent():
    """延迟加载 image_detection_agent"""
    global _agent
    if _agent is None:
        logger.info("正在加载 AI 模型...")
        from src.agents.image_detection_agent import agent as image_detection_agent
        _agent = image_detection_agent
        logger.info("AI 模型加载完成")
    return _agent


@app.on_event("startup")
async def startup_event():
    """启动时预加载模型"""
    logger.info("RuralBrain 服务启动中...")
    get_agent()  # 预加载模型
    logger.info("RuralBrain 服务启动完成")


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
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片接口
    
    Args:
        file: 上传的图片文件
        
    Returns:
        上传响应，包含文件路径
    """
    try:
        # 检查文件大小
        contents = await file.read()
        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制 ({MAX_UPLOAD_SIZE / 1024 / 1024}MB)",
            )
        
        # 检查文件扩展名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件格式，仅支持: {', '.join(ALLOWED_EXTENSIONS)}",
            )
        
        # 生成唯一文件名
        filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / filename
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"文件上传成功: {filename}")
        
        return UploadResponse(
            success=True,
            file_path=str(file_path),
            message="上传成功",
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
    流式对话接口
    
    Args:
        request: 聊天请求，包含消息和可选的图片路径
        
    Returns:
        SSE 流式响应
    """
    try:
        agent = get_agent()
        
        # 生成或使用线程ID
        thread_id = request.thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        # 构建消息内容
        message_content = request.message
        if request.image_path:
            # 如果有图片，在消息中包含图片路径
            message_content = f"{request.message}\n\n[图片路径: {request.image_path}]"
        
        logger.info(f"收到对话请求 [thread_id={thread_id}]: {request.message}")
        
        async def event_generator() -> AsyncGenerator[str, None]:
            """SSE 事件生成器"""
            try:
                # 发送开始事件
                yield f"data: {json.dumps({'type': 'start', 'thread_id': thread_id}, ensure_ascii=False)}\n\n"
                
                # 流式处理 agent 响应
                full_content = ""
                for chunk, metadata in agent.stream(
                    {"messages": [HumanMessage(content=message_content)]},
                    config,
                    stream_mode="messages",
                ):
                    # 只处理 AI 消息块
                    if isinstance(chunk, AIMessageChunk) and chunk.content:
                        full_content += chunk.content
                        
                        # 发送内容块
                        event_data = {
                            "type": "content",
                            "content": chunk.content,
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
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
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

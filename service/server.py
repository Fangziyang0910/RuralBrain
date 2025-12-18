"""
RuralBrain FastAPI 服务器
提供图像检测对话接口
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

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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

# 挂载静态文件目录，提供检测结果图片访问
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
        
        # 支持多图片路径（新版本）或单图片路径（兼容旧版本）
        image_paths = request.image_paths or ([request.image_path] if request.image_path else [])
        
        if image_paths:
            # 如果有图片，在消息中包含所有图片路径
            paths_text = "\n".join([f"[图片路径 {i+1}: {path}]" for i, path in enumerate(image_paths)])
            message_content = f"{request.message}\n\n{paths_text}"
        
        logger.info(f"收到对话请求 [thread_id={thread_id}]: {request.message}, 图片数量: {len(image_paths)}")
        
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

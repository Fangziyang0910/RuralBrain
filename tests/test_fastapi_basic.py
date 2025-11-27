#!/usr/bin/env python3
"""
FastAPI基础测试脚本
演示FastAPI的基本概念和如何封装现有功能
"""

import os
import sys
import json
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from uvicorn import run
import uvicorn

# 导入现有的检测工具
try:
    from src.tools.cow_detection_tool import cow_detection_tool
except ImportError:
    # 如果导入失败，创建一个模拟工具
    print("警告: 无法导入cow_detection_tool，使用模拟工具")
    
    async def mock_cow_detection_tool(file_path: str) -> str:
        """模拟牛检测工具"""
        return json.dumps({
            "success": True,
            "cow_count": 3,
            "cow_boxes": [
                {
                    'class': 'cow',
                    'confidence': 0.89,
                    'bbox': [100, 100, 200, 200],
                    'center': [150, 150]
                },
                {
                    'class': 'cow',
                    'confidence': 0.76,
                    'bbox': [300, 150, 400, 250],
                    'center': [350, 200]
                },
                {
                    'class': 'cow',
                    'confidence': 0.92,
                    'bbox': [200, 300, 300, 400],
                    'center': [250, 350]
                }
            ],
            "image_size": {"width": 640, "height": 480}
        }, ensure_ascii=False)
    
    cow_detection_tool = type('MockTool', (), {'invoke': mock_cow_detection_tool})()

# 创建FastAPI应用实例
app = FastAPI(
    title="牛识别系统API",
    description="基于YOLO和LangChain的牛识别与智能对话系统API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义Pydantic模型用于请求和响应
class ImageDetectionRequest(BaseModel):
    """图像检测请求模型"""
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="置信度阈值")
    return_image: bool = Field(default=False, description="是否返回标注后的图像")

class CowInfo(BaseModel):
    """牛信息模型"""
    id: int
    class_name: str = Field(default="cow", description="类别名称")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")
    bbox: Dict[str, float] = Field(description="边界框坐标")
    center: Dict[str, float] = Field(description="中心点坐标")

class ImageDetectionResponse(BaseModel):
    """图像检测响应模型"""
    success: bool = Field(description="检测是否成功")
    message: str = Field(description="响应消息")
    data: Optional[Dict[str, Any]] = Field(description="检测数据")

class ChatRequest(BaseModel):
    """对话请求模型"""
    message: str = Field(description="用户消息")
    thread_id: Optional[str] = Field(default="default", description="会话ID")
    image_path: Optional[str] = Field(default=None, description="图像路径")

class ChatResponse(BaseModel):
    """对话响应模型"""
    success: bool = Field(description="处理是否成功")
    message: str = Field(description="响应消息")
    data: Optional[Dict[str, Any]] = Field(description="响应数据")

# 定义服务类
class DetectionService:
    """检测服务类"""
    
    def __init__(self):
        """初始化检测服务"""
        self.temp_dir = tempfile.mkdtemp()
        print(f"创建临时目录: {self.temp_dir}")
    
    async def detect_image(self, file_path: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        检测图像中的牛只
        
        Args:
            file_path: 图像文件路径
            confidence_threshold: 置信度阈值
            
        Returns:
            检测结果字典
        """
        try:
            # 调用现有的检测工具
            result_str = cow_detection_tool.invoke(file_path)
            result = json.loads(result_str)
            
            # 根据置信度阈值过滤结果
            if result.get("success") and "cow_boxes" in result:
                filtered_cows = [
                    cow for cow in result["cow_boxes"]
                    if cow.get("confidence", 0) >= confidence_threshold
                ]
                result["cow_count"] = len(filtered_cows)
                result["cow_boxes"] = filtered_cows
            
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"检测处理失败: {str(e)}"
            }
    
    def save_upload_file(self, upload_file: UploadFile) -> str:
        """
        保存上传的文件
        
        Args:
            upload_file: 上传的文件对象
            
        Returns:
            保存后的文件路径
        """
        file_extension = os.path.splitext(upload_file.filename)[1]
        file_path = os.path.join(self.temp_dir, f"{upload_file.filename}_{os.urandom(8).hex()}{file_extension}")
        
        with open(file_path, "wb") as f:
            f.write(upload_file.file.read())
        
        return file_path
    
    def cleanup_temp_file(self, file_path: str) -> None:
        """
        清理临时文件
        
        Args:
            file_path: 文件路径
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"清理临时文件失败: {e}")

# 创建检测服务实例
detection_service = DetectionService()

# 定义依赖函数
async def get_detection_service() -> DetectionService:
    """获取检测服务实例"""
    return detection_service

# 定义路由
@app.get("/", tags=["根路径"])
async def root():
    """根路径，返回API信息"""
    return {
        "message": "牛识别系统API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": "2023-11-20T10:30:00Z",
        "version": "1.0.0",
        "model_loaded": True
    }

@app.post("/api/v1/detection/image", response_model=ImageDetectionResponse, tags=["检测"])
async def detect_cows_in_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    confidence_threshold: float = 0.5,
    return_image: bool = False,
    service: DetectionService = Depends(get_detection_service)
):
    """
    检测图像中的牛只
    
    Args:
        background_tasks: 后台任务
        file: 上传的图像文件
        confidence_threshold: 置信度阈值
        return_image: 是否返回标注后的图像
        service: 检测服务实例
        
    Returns:
        检测结果
    """
    # 验证文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="文件必须是图像格式")
    
    try:
        # 保存上传的文件
        file_path = service.save_upload_file(file)
        
        # 添加后台任务清理临时文件
        background_tasks.add_task(service.cleanup_temp_file, file_path)
        
        # 执行检测
        result = await service.detect_image(file_path, confidence_threshold)
        
        if result.get("success"):
            return ImageDetectionResponse(
                success=True,
                message="检测完成",
                data=result
            )
        else:
            return ImageDetectionResponse(
                success=False,
                message="检测失败",
                data=result
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")

@app.post("/api/v1/agent/chat", response_model=ChatResponse, tags=["对话"])
async def chat_with_agent(
    request: ChatRequest,
    service: DetectionService = Depends(get_detection_service)
):
    """
    与Agent进行对话
    
    Args:
        request: 对话请求
        service: 检测服务实例
        
    Returns:
        对话响应
    """
    try:
        # 这里应该集成现有的Agent功能
        # 为了演示，我们返回一个简单的响应
        
        response_text = f"收到您的消息: {request.message}"
        
        # 如果提供了图像路径，执行检测
        if request.image_path and os.path.exists(request.image_path):
            result = await service.detect_image(request.image_path)
            if result.get("success"):
                response_text += f"。检测到{result.get('cow_count', 0)}头牛。"
        
        return ChatResponse(
            success=True,
            message="对话完成",
            data={
                "response": response_text,
                "thread_id": request.thread_id,
                "detection_result": result if request.image_path else None
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")

# 主函数
if __name__ == "__main__":
    print("启动FastAPI测试服务器...")
    print("访问 http://127.0.0.1:8000/docs 查看API文档")
    print("访问 http://127.0.0.1:8000/redoc 查看ReDoc文档")
    
    # 运行服务器
    uvicorn.run(
        "test_fastapi_basic:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
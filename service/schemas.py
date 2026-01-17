"""
数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="消息角色: user/assistant")
    content: str = Field(..., description="消息内容")
    image_path: Optional[str] = Field(None, description="图片路径")


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    image_path: Optional[str] = Field(None, description="单图片路径（兼容旧版本）")
    image_paths: Optional[List[str]] = Field(None, description="多图片路径列表（新版本）")
    thread_id: Optional[str] = Field(None, description="对话线程ID")
    mode: Optional[str] = Field("auto", description="工作模式: auto/detection/planning")


class UploadResponse(BaseModel):
    """上传响应"""
    success: bool = Field(..., description="是否成功")
    file_path: Optional[str] = Field(None, description="单文件保存路径（兼容旧版本）")
    file_paths: Optional[List[str]] = Field(None, description="多文件保存路径列表（新版本）")
    message: Optional[str] = Field(None, description="消息")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误信息")

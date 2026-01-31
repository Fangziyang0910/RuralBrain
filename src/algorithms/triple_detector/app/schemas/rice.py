"""
大米识别数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class DetectionResult(BaseModel):
    """单个检测结果模型"""
    name: str
    count: int


class RicePredictionRequest(BaseModel):
    """大米品种识别请求模型"""
    image_base64: str = Field(..., description="Base64 编码的图片字符串")
    task_type: Optional[str] = Field(default="classification", description="任务类型，可选")


class RicePredictionResponse(BaseModel):
    """大米品种识别响应模型"""
    success: bool
    detections: List[DetectionResult]
    result_image: Optional[str] = Field(None, description="标注好的结果图片(Base64)")
    message: Optional[str] = None

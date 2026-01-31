"""
病虫害检测数据模型
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import base64


class Detection(BaseModel):
    """单个检测结果模型"""
    name: str = Field(..., description="害虫类别名称", example="瓜实蝇")
    count: int = Field(..., description="检测到的数量", example=2, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "瓜实蝇",
                "count": 2
            }
        }


class DetectRequest(BaseModel):
    """害虫检测请求模型"""
    image_base64: str = Field(
        ...,
        description="图像的base64编码字符串（不包含data:image/jpeg;base64,前缀）",
        example="/9j/4AAQSkZJRgABAQEAYGBgY...",
        min_length=1000
    )

    @validator('image_base64')
    def validate_base64(cls, v):
        """验证base64编码格式"""
        try:
            base64.b64decode(v, validate=True)
            return v
        except Exception:
            raise ValueError("无效的base64编码格式")

    @validator('image_base64')
    def validate_image_size(cls, v):
        """验证图像大小（估计）"""
        try:
            decoded = base64.b64decode(v)
            estimated_size = len(decoded)
            if estimated_size > 50 * 1024 * 1024:
                raise ValueError("图像文件过大，请压缩后上传（最大50MB）")
            return v
        except Exception:
            return v

    class Config:
        json_schema_extra = {
            "example": {
                "image_base64": "/9j/4AAQSkZJRgABAQEAYGBgY..."
            }
        }


class DetectResponse(BaseModel):
    """害虫检测响应模型"""
    success: bool = Field(True, description="检测是否成功")
    detections: List[Detection] = Field(default=[], description="检测到的害虫列表")
    result_image: str = Field(..., description="标注了检测框的图像（base64编码）")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "detections": [
                    {
                        "name": "瓜实蝇",
                        "count": 2
                    },
                    {
                        "name": "蚜虫",
                        "count": 1
                    }
                ],
                "result_image": "/9j/4AAQSkZJRgABAQEAYGBgY..."
            }
        }


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="请求是否成功")
    message: str = Field(..., description="错误信息", example="无效的base64编码格式")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "无效的base64编码格式"
            }
        }

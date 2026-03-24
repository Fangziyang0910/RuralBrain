"""
疾病图片识别数据模型
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import base64


class DiseaseDetection(BaseModel):
    """单个疾病检测结果模型"""
    name: str = Field(..., description="疾病类别名称", example="cow_healthy")
    confidence: float = Field(..., description="置信度", example=0.85, ge=0, le=1)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "cow_healthy",
                "confidence": 0.85
            }
        }


class DiseaseDetectRequest(BaseModel):
    """疾病检测请求模型"""
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


class DiseaseDetectResponse(BaseModel):
    """疾病检测响应模型"""
    success: bool = Field(True, description="检测是否成功")
    detections: List[DiseaseDetection] = Field(default=[], description="检测到的疾病列表")
    result_image: str = Field(..., description="标注了检测框的图像（base64编码）")
    primary_disease: Optional[str] = Field(None, description="主要检测到的疾病")
    animal_type: Optional[str] = Field(None, description="识别的动物类型 (cow/pig/chicken等)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "detections": [
                    {
                        "name": "cow_healthy",
                        "confidence": 0.92
                    },
                    {
                        "name": "cow_lumpy",
                        "confidence": 0.08
                    }
                ],
                "result_image": "/9j/4AAQSkZJRgABAQEAYGBgY...",
                "primary_disease": "cow_healthy",
                "animal_type": "cow"
            }
        }


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="请求是否成功")
    error: str = Field(..., description="错误信息", example="模型未加载")
    message: str = Field(..., description="用户友好的错误描述", example="疾病识别模型尚未准备好，请稍后重试")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Model not loaded",
                "message": "疾病识别模型尚未准备好，请稍后重试"
            }
        }

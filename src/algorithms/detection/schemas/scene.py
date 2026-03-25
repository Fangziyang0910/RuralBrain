"""
场景分类数据模型
支持：牛舍、猪舍、农田
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import base64


class SceneClassifyRequest(BaseModel):
    """场景分类请求模型"""
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

    class Config:
        json_schema_extra = {
            "example": {
                "image_base64": "/9j/4AAQSkZJRgABAQEAYGBgY..."
            }
        }


class SceneClassifyResponse(BaseModel):
    """场景分类响应模型"""
    success: bool = Field(True, description="分类是否成功")
    scene_type: str = Field(..., description="场景类型 (cattle/pig/farmland/unknown)")
    scene_name: str = Field(..., description="场景名称 (牛舍/猪舍/农田/未知)")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    recommended_tools: Optional[List[dict]] = Field(default=[], description="建议的后续工具")
    mock: bool = Field(default=False, description="是否为模拟结果（模型未训练时）")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "scene_type": "cattle",
                "scene_name": "牛舍",
                "confidence": 0.95,
                "recommended_tools": [
                    {"tool": "cow_detection_tool", "reason": "检测牛只数量"},
                    {"tool": "disease_prediction_tool", "reason": "分析牛只健康状况"}
                ],
                "mock": False
            }
        }


class SupportedScenesResponse(BaseModel):
    """支持的场景类别响应"""
    supported_scenes: List[dict] = Field(..., description="支持的场景类别列表")
    total_classes: int = Field(..., description="场景类别总数")
    model_loaded: bool = Field(..., description="模型是否已加载")

    class Config:
        json_schema_extra = {
            "example": {
                "supported_scenes": [
                    {"type": "cattle", "name": "牛舍", "description": "奶牛养殖区域"},
                    {"type": "pig", "name": "猪舍", "description": "生猪养殖区域"},
                    {"type": "farmland", "name": "农田", "description": "农作物种植区域"}
                ],
                "total_classes": 3,
                "model_loaded": True
            }
        }

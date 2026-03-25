"""
植物病害识别数据模型
基于百度飞桨2018年农作物病害数据集
支持10种植物，61个分类
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import base64


class PlantDiseaseDetectRequest(BaseModel):
    """植物病害检测请求模型"""
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


class PlantDiseaseDetectResponse(BaseModel):
    """植物病害检测响应模型"""
    success: bool = Field(True, description="检测是否成功")
    class_id: int = Field(..., description="类别ID (0-60)", ge=-1, le=60)
    disease_name: str = Field(..., description="病害名称", example="番茄晚疫病菌（一般）")
    crop: str = Field(..., description="作物种类", example="番茄")
    disease: str = Field(..., description="病害类型", example="晚疫病")
    severity: str = Field(..., description="严重程度 (一般/严重/无)", example="一般")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    mock: bool = Field(default=False, description="是否为模拟结果（模型未训练时）")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "class_id": 48,
                "disease_name": "番茄晚疫病菌（一般）",
                "crop": "番茄",
                "disease": "晚疫病",
                "severity": "一般",
                "confidence": 0.88,
                "mock": False
            }
        }


class SupportedPlantDiseasesResponse(BaseModel):
    """支持的植物病害类别响应"""
    supported_diseases: List[dict] = Field(..., description="支持的病害类别列表")
    total_classes: int = Field(..., description="病害类别总数")
    model_loaded: bool = Field(..., description="模型是否已加载")
    crops: List[str] = Field(..., description="支持的作物种类")

    class Config:
        json_schema_extra = {
            "example": {
                "supported_diseases": [
                    {"class_id": 0, "name": "苹果（健康）", "crop": "苹果", "disease": "健康", "severity": "无"},
                    {"class_id": 1, "name": "苹果黑星病（一般）", "crop": "苹果", "disease": "黑星病", "severity": "一般"}
                ],
                "total_classes": 61,
                "model_loaded": True,
                "crops": ["苹果", "樱桃", "葡萄", "柑桔", "桃", "草莓", "番茄", "辣椒", "玉米", "马铃薯"]
            }
        }

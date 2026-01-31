"""
奶牛检测数据模型
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import base64


class Detection(BaseModel):
    """单个检测结果模型"""
    name: str = Field(..., description="牛只类别名称", example="奶牛")
    count: int = Field(..., description="检测到的数量", example=2, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "奶牛",
                "count": 2
            }
        }


class DetectRequest(BaseModel):
    """牛只检测请求模型"""
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
    """牛只检测响应模型"""
    success: bool = Field(True, description="检测是否成功")
    detections: List[Detection] = Field(default=[], description="检测到的牛只列表")
    result_image: str = Field(..., description="标注了检测框的图像（base64编码）")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "detections": [
                    {
                        "name": "奶牛",
                        "count": 3
                    }
                ],
                "result_image": "/9j/4AAQSkZJRgABAQEAYGBgY..."
            }
        }


class DetectionSize(BaseModel):
    """检测对象大小模型"""
    width: float = Field(..., description="宽度(像素)")
    height: float = Field(..., description="高度(像素)")
    area: float = Field(..., description="面积(平方像素)")


class RelativePosition(BaseModel):
    """相对位置模型"""
    x: float = Field(..., description="相对x位置 (0-1)")
    y: float = Field(..., description="相对y位置 (0-1)")


class DetailedDetection(BaseModel):
    """详细检测结果模型"""
    class_name: str = Field(..., description="类别名称")
    confidence: float = Field(..., description="置信度")
    bbox: List[float] = Field(..., description="边界框坐标 [x1, y1, x2, y2]")
    center: List[float] = Field(..., description="中心点坐标 [x, y]")
    size: DetectionSize = Field(..., description="牛只大小信息")
    relative_position: RelativePosition = Field(..., description="相对位置信息")


class ImageInfo(BaseModel):
    """图像信息模型"""
    width: int = Field(..., description="图像宽度(像素)")
    height: int = Field(..., description="图像高度(像素)")
    total_cows: int = Field(..., description="检测到的牛只总数")


class DetailedDetectResponse(BaseModel):
    """详细牛只检测响应模型"""
    success: bool = Field(True, description="检测是否成功")
    detections: List[Detection] = Field(default=[], description="检测到的牛只列表(按类别统计)")
    detailed_detections: List[DetailedDetection] = Field(default=[], description="详细的检测信息列表")
    image_info: ImageInfo = Field(..., description="图像信息")
    result_image: str = Field(..., description="标注了检测框的图像（base64编码）")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "detections": [
                    {
                        "name": "奶牛",
                        "count": 3
                    }
                ],
                "detailed_detections": [
                    {
                        "class_name": "奶牛",
                        "confidence": 0.95,
                        "bbox": [100, 100, 200, 200],
                        "center": [150, 150],
                        "size": {
                            "width": 100,
                            "height": 100,
                            "area": 10000
                        },
                        "relative_position": {
                            "x": 0.15,
                            "y": 0.15
                        }
                    }
                ],
                "image_info": {
                    "width": 1920,
                    "height": 1080,
                    "total_cows": 3
                },
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

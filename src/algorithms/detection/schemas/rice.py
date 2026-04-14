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


# ==================== 详细检测模型 ====================

class DetectionSize(BaseModel):
    """检测对象大小模型"""
    width: float = Field(..., description="宽度(像素)")
    height: float = Field(..., description="高度(像素)")
    area: float = Field(..., description="面积(平方像素)")


class RelativePosition(BaseModel):
    """相对位置模型"""
    x: float = Field(..., description="相对x位置 (0-1)")
    y: float = Field(..., description="相对y位置 (0-1)")


class RiceDetailedDetection(BaseModel):
    """详细大米检测结果模型"""
    class_name: str = Field(..., description="大米品种名称")
    confidence: float = Field(..., description="置信度 (0-1)")
    bbox: List[float] = Field(..., description="边界框坐标 [x1, y1, x2, y2]")
    center: List[float] = Field(..., description="中心点坐标 [x, y]")
    size: DetectionSize = Field(..., description="大米颗粒大小信息")
    relative_position: RelativePosition = Field(..., description="相对位置信息")


class RiceImageInfo(BaseModel):
    """大米图像信息模型"""
    width: int = Field(..., description="图像宽度(像素)")
    height: int = Field(..., description="图像高度(像素)")
    total_rice: int = Field(..., description="检测到的米粒总数")


class RiceDetailedDetectResponse(BaseModel):
    """详细大米检测响应模型"""
    success: bool = Field(True, description="检测是否成功")
    detections: List[DetectionResult] = Field(default=[], description="检测到的品种列表(按品种统计)")
    detailed_detections: List[RiceDetailedDetection] = Field(default=[], description="详细的检测信息列表")
    image_info: RiceImageInfo = Field(..., description="图像信息")
    result_image: str = Field(..., description="标注了检测框的图像（base64编码）")
    avg_confidence: float = Field(..., description="平均置信度")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "detections": [
                    {"name": "珍珠大米", "count": 12},
                    {"name": "丝苗米", "count": 8}
                ],
                "detailed_detections": [
                    {
                        "class_name": "珍珠大米",
                        "confidence": 0.92,
                        "bbox": [100, 100, 150, 150],
                        "center": [125, 125],
                        "size": {"width": 50, "height": 50, "area": 2500},
                        "relative_position": {"x": 0.125, "y": 0.125}
                    }
                ],
                "image_info": {
                    "width": 1920,
                    "height": 1080,
                    "total_rice": 20
                },
                "result_image": "/9j/4AAQSkZJRgABAQEAYGBgY...",
                "avg_confidence": 0.89
            }
        }

from pydantic import BaseModel, Field
from typing import List, Optional

class RicePredictionRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 编码的图片字符串")
    task_type: Optional[str] = Field(default="classification", description="任务类型，可选")

class DetectionResult(BaseModel):
    name: str
    count: int

class RicePredictionResponse(BaseModel):
    success: bool
    detections: List[DetectionResult]
    result_image: Optional[str] = None
    message: Optional[str] = None
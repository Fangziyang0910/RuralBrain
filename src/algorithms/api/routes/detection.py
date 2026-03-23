"""
检测算法路由

将检测算法的服务接口注册到 FastAPI。
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 导入检测算法服务（纯算法代码）
# 注意：这些服务不依赖 FastAPI，可以独立测试
from algorithms.detection.services.pest_service import pest_service
from algorithms.detection.services.rice_service import rice_service
from algorithms.detection.services.cow_service import cow_service
from algorithms.detection.services.disease_service import disease_service

# 导入数据模型
from algorithms.detection.schemas.pest import DetectRequest as PestDetectionRequest, DetectResponse as PestDetectionResponse
from algorithms.detection.schemas.rice import RicePredictionRequest as RiceDetectionRequest, RicePredictionResponse as RiceDetectionResponse
from algorithms.detection.schemas.cow import DetectRequest as CowDetectionRequest, DetectResponse as CowDetectionResponse
from algorithms.detection.schemas.disease import DiseaseDetectRequest, DiseaseDetectResponse


# ==================== 病虫害检测 ====================

@router.post("/pest/detect", response_model=PestDetectionResponse)
async def detect_pests(request: PestDetectionRequest):
    """
    检测农作物病虫害

    Args:
        request: 包含 base64 编码的图片数据

    Returns:
        病虫害检测结果
    """
    try:
        result = pest_service.detect(request.image_base64)
        return result
    except Exception as e:
        logger.error(f"病虫害检测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pest/supported-pests")
async def get_supported_pests():
    """获取支持的病虫害种类"""
    return pest_service.get_supported_pests()


# ==================== 大米识别 ====================

@router.post("/rice/predict", response_model=RiceDetectionResponse)
async def predict_rice(request: RiceDetectionRequest):
    """
    识别大米品种

    Args:
        request: 包含 base64 编码的图片数据

    Returns:
        大米品种识别结果
    """
    try:
        result = rice_service.predict(request.image_base64)
        return result
    except Exception as e:
        logger.error(f"大米识别失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rice/supported-rice-types")
async def get_supported_rice_types():
    """获取支持的大米品种"""
    return rice_service.get_supported_rice_types()


# ==================== 奶牛检测 ====================

@router.post("/cow/detect", response_model=CowDetectionResponse)
async def detect_cows(request: CowDetectionRequest):
    """
    检测图片中的奶牛

    Args:
        request: 包含 base64 编码的图片数据

    Returns:
        奶牛检测结果
    """
    try:
        result = cow_service.detect(request.image_base64)
        return result
    except Exception as e:
        logger.error(f"奶牛检测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cow/supported-cows")
async def get_supported_cows():
    """获取支持的奶牛品种"""
    return cow_service.get_supported_cows()


# ==================== 疾病检测 ====================

@router.post("/disease/detect", response_model=DiseaseDetectResponse)
async def detect_diseases(request: DiseaseDetectRequest):
    """
    检测图片中的疾病患处

    根据患处图片识别动物疾病类型，支持牛、猪等畜禽疾病识别。

    Args:
        request: 包含 base64 编码的图片数据

    Returns:
        疾病检测结果，包含识别的疾病类别、置信度、动物类型等
    """
    try:
        result = disease_service.detect(request.image_base64)
        return result
    except Exception as e:
        logger.error(f"疾病检测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disease/supported-diseases")
async def get_supported_diseases():
    """获取支持的疾病类别"""
    return disease_service.get_supported_diseases()

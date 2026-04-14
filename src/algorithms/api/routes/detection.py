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
from algorithms.detection.services.scene_service import scene_service
from algorithms.detection.services.plant_disease_service import plant_disease_service

# 导入数据模型
from algorithms.detection.schemas.pest import DetectRequest as PestDetectionRequest, DetectResponse as PestDetectionResponse
from algorithms.detection.schemas.rice import (
    RicePredictionRequest as RiceDetectionRequest,
    RicePredictionResponse as RiceDetectionResponse,
    RiceDetailedDetectResponse
)
from algorithms.detection.schemas.cow import (
    DetectRequest as CowDetectionRequest,
    DetectResponse as CowDetectionResponse,
    DetailedDetectResponse
)
from algorithms.detection.schemas.disease import DiseaseDetectRequest, DiseaseDetectResponse
from algorithms.detection.schemas.scene import SceneClassifyRequest, SceneClassifyResponse, SupportedScenesResponse
from algorithms.detection.schemas.plant_disease import PlantDiseaseDetectRequest, PlantDiseaseDetectResponse, SupportedPlantDiseasesResponse


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


@router.post("/rice/predict_detailed", response_model=RiceDetailedDetectResponse)
async def predict_rice_detailed(request: RiceDetectionRequest):
    """
    详细大米品种识别

    返回完整的检测信息，包括：
    - 每粒米的边界框坐标 (bbox)
    - 置信度 (confidence)
    - 品种分布统计

    Args:
        request: 包含 base64 编码的图片数据

    Returns:
        详细大米检测结果
    """
    try:
        result = rice_service.detect_detailed(request.image_base64)
        return result
    except Exception as e:
        logger.error(f"大米详细识别失败: {e}")
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


@router.post("/cow/detect_detailed", response_model=DetailedDetectResponse)
async def detect_cows_detailed(request: CowDetectionRequest):
    """
    检测图片中的奶牛（详细模式）

    返回完整的检测信息，包括：
    - 每头牛的边界框坐标 (bbox)
    - 置信度 (confidence)
    - 牛只大小和位置信息

    Args:
        request: 包含 base64 编码的图片数据

    Returns:
        详细奶牛检测结果
    """
    try:
        result = cow_service.detect_detailed(request.image_base64)
        return result
    except Exception as e:
        logger.error(f"奶牛详细检测失败: {e}")
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


# ==================== 场景分类 ====================

@router.post("/scene/classify", response_model=SceneClassifyResponse)
async def classify_scene(request: SceneClassifyRequest):
    """
    分类农场巡检图片的场景类型

    支持识别三种场景：
    - 牛舍 (cattle)：建议调用牛只检测和疾病预测工具
    - 猪舍 (pig)：建议调用疾病预测工具
    - 农田 (farmland)：建议调用病虫害和植物病害检测工具

    Args:
        request: 包含 base64 编码的图片数据

    Returns:
        场景分类结果和建议的后续工具
    """
    try:
        result = scene_service.classify(request.image_base64)
        return result
    except Exception as e:
        logger.error(f"场景分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scene/supported-scenes", response_model=SupportedScenesResponse)
async def get_supported_scenes():
    """获取支持的场景类别"""
    return scene_service.get_supported_scenes()


# ==================== 植物病害识别 ====================

@router.post("/plant_disease/detect", response_model=PlantDiseaseDetectResponse)
async def detect_plant_disease(request: PlantDiseaseDetectRequest):
    """
    识别农作物病害

    基于**百度飞桨2018年农作物病害数据集**，支持10种植物的病害识别：
    - 苹果、樱桃、葡萄、柑桔、桃、草莓、番茄、辣椒、玉米、马铃薯
    - 共61个分类（包含一般/严重程度）

    Args:
        request: 包含 base64 编码的图片数据

    Returns:
        植物病害检测结果，包含作物种类、病害类型、严重程度等
    """
    try:
        result = plant_disease_service.detect(request.image_base64)
        return result
    except Exception as e:
        logger.error(f"植物病害检测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plant_disease/supported-diseases", response_model=SupportedPlantDiseasesResponse)
async def get_supported_plant_diseases():
    """获取支持的植物病害类别"""
    return plant_disease_service.get_supported_diseases()

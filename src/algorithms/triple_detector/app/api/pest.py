"""
病虫害检测路由
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from typing import Union

from app.schemas.pest import DetectRequest, DetectResponse, ErrorResponse
from app.services.pest_service import pest_model_service
from app.core.config import settings

import logging
import traceback
import os

router = APIRouter()

# 预定义的害虫类别（当文件不存在时使用）
DEFAULT_PEST_CLASSES = [
    {"id": 0, "chinese_name": "瓜实蝇", "english_name": "Melon fly"},
    {"id": 1, "chinese_name": "小菜蛾", "english_name": "Diamondback moth"},
    {"id": 2, "chinese_name": "斑潜蝇", "english_name": "Leafminer fly"},
    {"id": 3, "chinese_name": "侧多食跗线螨", "english_name": "Tarsonemid mite"},
    {"id": 4, "chinese_name": "稻粉虱", "english_name": "Rice whitefly"},
]


@router.post(
    "/detect",
    response_model=DetectResponse,
    status_code=status.HTTP_200_OK,
    summary="🐛 智能害虫检测",
    description="使用YOLOv8深度学习模型进行害虫检测和识别",
    tags=["病虫害检测"]
)
async def detect_pests(request: DetectRequest) -> Union[DetectResponse, JSONResponse]:
    """智能害虫检测接口"""

    try:
        logging.info(f"[Pest] 开始害虫检测，图像大小: {len(request.image_base64)} 字符")

        # 调用模型服务进行检测
        detections, result_image_b64 = pest_model_service.process_image_from_base64(request.image_base64)

        # 构造成功响应
        logging.info(f"[Pest] 检测成功，发现 {len(detections)} 种害虫")

        return DetectResponse(
            success=True,
            detections=detections or [],
            result_image=result_image_b64
        )

    except ValueError as ve:
        # 参数验证错误
        error_msg = str(ve)
        logging.warning(f"[Pest] 参数验证错误: {error_msg}")

        if "base64" in error_msg.lower():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "无效的base64编码格式，请检查图像数据"
                }
            )
        elif "格式" in error_msg:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "不支持的图像格式，支持JPEG、PNG、BMP格式"
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": f"输入参数错误: {error_msg}"
                }
            )

    except FileNotFoundError as fnfe:
        # 模型文件不存在
        error_msg = "模型文件未找到，请联系管理员"
        logging.error(f"[Pest] 模型文件错误: {str(fnfe)}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": error_msg
            }
        )

    except MemoryError:
        # 内存不足
        error_msg = "图像过大或服务器内存不足，请压缩图像后重试"
        logging.error("[Pest] 内存不足错误")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": error_msg
            }
        )

    except Exception as e:
        # 其他未预期错误
        error_msg = "服务器内部错误，请稍后重试"
        logging.error(f"[Pest] 未预期错误: {str(e)}\n{traceback.format_exc()}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": error_msg
            }
        )


@router.get(
    "/supported-pests",
    summary="获取支持的害虫类型列表",
    description="返回当前模型支持检测的所有害虫类型",
    tags=["病虫害检测 - 系统信息"]
)
async def get_supported_pests():
    """获取支持的害虫类型列表"""
    try:
        # 读取害虫类别文件
        pest_classes = []
        try:
            with open(settings.PEST_CLASSES_PATH, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if line:
                        parts = line.split()
                        if len(parts) >= 2:
                            chinese_name = parts[-1]
                            english_name = " ".join(parts[:-1])
                        else:
                            chinese_name = line
                            english_name = line

                        pest_classes.append({
                            "id": i,
                            "chinese_name": chinese_name,
                            "english_name": english_name,
                            "full_name": line
                        })
        except FileNotFoundError:
            # 如果文件不存在，返回默认类别
            pest_classes = DEFAULT_PEST_CLASSES

        return {
            "success": True,
            "total_count": len(pest_classes),
            "pest_classes": pest_classes,
            "model_info": {
                "version": "YOLOv8",
                "last_updated": "2024-11-28"
            }
        }

    except Exception as e:
        logging.error(f"[Pest] 获取害虫类别失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "获取害虫类别列表失败"
            }
        )

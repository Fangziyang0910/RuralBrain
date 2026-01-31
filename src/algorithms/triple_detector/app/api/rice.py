"""
大米品种识别路由
"""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from typing import Union

from app.schemas.rice import RicePredictionRequest, RicePredictionResponse
from app.services.rice_service import rice_service

import logging
import traceback

router = APIRouter()


@router.post(
    "/predict",
    response_model=RicePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="🌾 大米品种识别",
    description="使用YOLOv8模型进行大米品种识别",
    tags=["大米识别"]
)
async def predict_rice(request: RicePredictionRequest) -> Union[RicePredictionResponse, JSONResponse]:
    """大米品种识别接口"""

    try:
        logging.info(f"[Rice] 开始大米品种识别，图像大小: {len(request.image_base64)} 字符")

        # 调用模型服务进行识别
        result = rice_service.predict(request.image_base64)

        # 构造成功响应
        logging.info(f"[Rice] 识别成功，发现 {len(result.get('detections', []))} 种大米品种")

        return RicePredictionResponse(
            success=result.get('success', False),
            detections=result.get('detections', []),
            result_image=result.get('result_image'),
            message=result.get('message')
        )

    except ValueError as ve:
        # 参数验证错误
        error_msg = str(ve)
        logging.warning(f"[Rice] 参数验证错误: {error_msg}")

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "detections": [],
                "message": error_msg
            }
        )

    except FileNotFoundError as fnfe:
        # 模型文件不存在
        error_msg = "模型文件未找到，请联系管理员"
        logging.error(f"[Rice] 模型文件错误: {str(fnfe)}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "detections": [],
                "message": error_msg
            }
        )

    except Exception as e:
        # 其他未预期错误
        error_msg = "服务器内部错误，请稍后重试"
        logging.error(f"[Rice] 未预期错误: {str(e)}\n{traceback.format_exc()}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "detections": [],
                "message": error_msg
            }
        )


@router.get(
    "/supported-rice-types",
    summary="获取支持的大米品种列表",
    description="返回当前模型支持识别的所有大米品种类型",
    tags=["大米识别 - 系统信息"]
)
async def get_supported_rice_types():
    """获取支持的大米品种列表"""
    try:
        rice_types = [
            {"id": 1, "name": "糯米"},
            {"id": 2, "name": "丝苗米"},
            {"id": 3, "name": "泰国香米"},
            {"id": 4, "name": "五常大米"},
            {"id": 5, "name": "珍珠大米"}
        ]

        return {
            "success": True,
            "total_count": len(rice_types),
            "rice_types": rice_types,
            "model_info": {
                "version": "YOLOv8",
                "last_updated": "2024-11-28"
            }
        }

    except Exception as e:
        logging.error(f"[Rice] 获取大米品种列表失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "获取大米品种列表失败"
            }
        )

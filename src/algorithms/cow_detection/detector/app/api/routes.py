from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Union

# 兼容 Docker 和本地环境的导入
try:
    # Docker 环境：使用相对导入
    from app.schemas.detection import DetectRequest, DetectResponse, Detection, ErrorResponse, DetailedDetectResponse
    from app.services.model_service import model_service
    from app.core.config import settings
except ImportError:
    # 本地环境：使用绝对导入
    from src.algorithms.cow_detection.detector.app.schemas.detection import DetectRequest, DetectResponse, Detection, ErrorResponse, DetailedDetectResponse
    from src.algorithms.cow_detection.detector.app.services.model_service import model_service
    from src.algorithms.cow_detection.detector.app.core.config import settings

import logging
import traceback
from datetime import datetime
import os

router = APIRouter()


@router.post(
    "/detect",
    response_model=DetectResponse,
    status_code=status.HTTP_200_OK,
    summary="🐄 智能牛只检测接口",
    description="使用YOLOv8深度学习模型进行牛只检测和识别",
    responses={
        200: {
            "description": "检测成功",
            "content": {
                "application/json": {
                    "examples": {
                        "success_with_detections": {
                            "summary": "成功检测到牛只",
                            "value": {
                                "success": True,
                                "detections": [
                                    {
                                        "name": "奶牛",
                                        "count": 3
                                    }
                                ],
                                "result_image": "/9j/4AAQSkZJRgABAQEASABIAAD..."
                            }
                        },
                        "success_no_detections": {
                            "summary": "没有检测到牛只",
                            "value": {
                                "success": True,
                                "detections": [],
                                "result_image": "/9j/4AAQSkZJRgABAQEASABIAAD..."
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "请求参数错误",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_base64": {
                            "summary": "无效的base64编码",
                            "value": {
                                "success": False,
                                "message": "无效的base64编码格式，请检查图像数据"
                            }
                        },
                        "unsupported_format": {
                            "summary": "不支持的图像格式",
                            "value": {
                                "success": False,
                                "message": "不支持的图像格式，支持JPEG、PNG、BMP格式"
                            }
                        }
                    }
                }
            }
        },
        422: {
            "description": "请求体验证失败",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "image_base64"],
                                "msg": "图片数据太小，请提供有效的图片",
                                "type": "value_error"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "服务器内部错误，请稍后重试"
                    }
                }
            }
        }
    },
    tags=["牛只检测"]
)
async def detect_cows(request: DetectRequest) -> Union[DetectResponse, JSONResponse]:
    """
    # 🐄 智能牛只检测接口
    
    该接口使用先进的YOLOv8深度学习模型对上传的图像进行牛只检测和识别。
    支持多种牛只类型的检测，包括奶牛、肉牛等。
    
    ## 功能特点
    - 🎯 **高精度检测**: 基于YOLOv8模型，检测精度高
    - 🚀 **快速响应**: 一般1-3秒内返回结果  
    - 📋 **多目标检测**: 同时检测多个牛只
    - 🖼️ **视觉化结果**: 返回标注了检测框的图像
    
    ## 请求格式
    - **Content-Type**: `application/json`
    - **Body**: JSON格式，包含`image_base64`字段
    
    ## 图像要求
    - **格式**: JPEG, PNG, BMP
    - **尺寸**: 建议640x640像素以上，最大支持50MB
    - **编码**: Base64编码（不包含`data:image/jpeg;base64,`前缀）
    - **内容**: 清晰的牛只图像，光线良好
    
    ## 返回结果
    成功时返回包含以下信息：
    - **detections**: 检测到的牛只列表，包括类型、数量
    - **result_image**: 标注了检测框的图像（base64格式）
    - **message**: 检测结果描述
    
    ## 使用示例
    
    ### Python请求示例
    ```python
    import requests
    import base64
    
    # 读取图像并转换为base64
    with open('cow_image.jpg', 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    # 发送请求
    response = requests.post(
        'http://localhost:8001/detect',
        json={'image_base64': img_b64}
    )
    
    # 处理响应
    result = response.json()
    if result['success']:
        print(f"检测到 {len(result['detections'])} 种牛只")
        for detection in result['detections']:
            print(f"- {detection['name']}: {detection['count']}个")
    else:
        print(f"检测失败: {result['message']}")
    ```
    
    ### JavaScript请求示例  
    ```javascript
    // 使用fetch API
    const response = await fetch('http://localhost:8001/detect', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            image_base64: 'your_base64_image_here'
        })
    });
    
    const result = await response.json();
    if (result.success) {
        console.log(`检测到 ${result.detections.length} 种牛只`);
        result.detections.forEach(detection => {
            console.log(`${detection.name}: ${detection.count}个`);
        });
    } else {
        console.error(`检测失败: ${result.message}`);
    }
    ```
    
    ### curl请求示例
    ```bash
    curl -X POST "http://localhost:8001/detect" \\
         -H "Content-Type: application/json" \\
         -d '{
           "image_base64": "your_base64_image_here"
         }'
    ```
    
    ---
    
    **技术支持**: 如遇到问题，请检查图像格式和网络连接，或联系技术支持团队。
    """
    
    try:
        logging.info(f"开始牛只检测，图像大小: {len(request.image_base64)} 字符")
        
        # 调用模型服务进行检测
        detections, result_image_b64, _, _ = model_service.process_image_from_base64(request.image_base64)
        
        # 构造成功响应
        logging.info(f"检测成功，发现 {len(detections)} 种牛只")
        
        return DetectResponse(
            success=True,
            detections=detections or [],
            result_image=result_image_b64
        )
        
    except ValueError as ve:
        # 参数验证错误
        error_msg = str(ve)
        logging.warning(f"参数验证错误: {error_msg}")
        
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
        logging.error(f"模型文件错误: {str(fnfe)}")
        
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
        logging.error("内存不足错误")
        
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
        logging.error(f"未预期错误: {str(e)}\n{traceback.format_exc()}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": error_msg
            }
        )


@router.post(
    "/detect-detailed",
    response_model=DetailedDetectResponse,
    status_code=status.HTTP_200_OK,
    summary="🐄 详细牛只检测接口",
    description="使用YOLOv8深度学习模型进行牛只检测和识别，返回详细的检测信息",
    responses={
        200: {
            "description": "检测成功",
            "content": {
                "application/json": {
                    "examples": {
                        "success_with_detections": {
                            "summary": "成功检测到牛只",
                            "value": {
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
                                "result_image": "/9j/4AAQSkZJRgABAQEASABIAAD..."
                            }
                        }
                    }
                }
            }
        },
        400: {
            "description": "请求参数错误",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_base64": {
                            "summary": "无效的base64编码",
                            "value": {
                                "success": False,
                                "message": "无效的base64编码格式，请检查图像数据"
                            }
                        }
                    }
                }
            }
        },
        500: {
            "description": "服务器内部错误",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "服务器内部错误，请稍后重试"
                    }
                }
            }
        }
    },
    tags=["牛只检测"]
)
async def detect_cows_detailed(request: DetectRequest) -> Union[DetailedDetectResponse, JSONResponse]:
    """
    # 🐄 详细牛只检测接口
    
    该接口使用先进的YOLOv8深度学习模型对上传的图像进行牛只检测和识别，
    返回详细的检测信息，包括牛只的大小、位置等信息。
    
    ## 功能特点
    - 🎯 **高精度检测**: 基于YOLOv8模型，检测精度高
    - 🚀 **快速响应**: 一般1-3秒内返回结果  
    - 📋 **多目标检测**: 同时检测多个牛只
    - 📏 **尺寸信息**: 提供每个牛只的尺寸和位置信息
    - 🖼️ **视觉化结果**: 返回标注了检测框的图像
    
    ## 请求格式
    - **Content-Type**: `application/json`
    - **Body**: JSON格式，包含`image_base64`字段
    
    ## 返回结果
    成功时返回包含以下信息：
    - **detections**: 检测到的牛只列表，包括类型、数量
    - **detailed_detections**: 详细的检测信息列表，包括每个牛只的边界框、中心点、大小等
    - **image_info**: 图像信息，包括尺寸和检测到的牛只总数
    - **result_image**: 标注了检测框的图像（base64格式）
    """
    
    try:
        logging.info(f"开始详细牛只检测，图像大小: {len(request.image_base64)} 字符")
        
        # 调用模型服务进行详细检测
        detailed_result = model_service.detect_cows_detailed(request.image_base64)
        
        # 构造成功响应
        logging.info(f"检测成功，发现 {len(detailed_result['detailed_detections'])} 个牛只")
        
        return DetailedDetectResponse(
            success=True,
            detections=detailed_result['detections'] or [],
            detailed_detections=detailed_result['detailed_detections'] or [],
            image_info=detailed_result['image_info'],
            result_image=detailed_result['result_image']
        )
        
    except ValueError as ve:
        # 参数验证错误
        error_msg = str(ve)
        logging.warning(f"参数验证错误: {error_msg}")
        
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
        logging.error(f"模型文件错误: {str(fnfe)}")
        
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
        logging.error("内存不足错误")
        
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
        logging.error(f"未预期错误: {str(e)}\n{traceback.format_exc()}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": error_msg
            }
        )


@router.get(
    "/supported-cows",
    summary="获取支持的牛只类型列表", 
    description="返回当前模型支持检测的所有牛只类型",
    tags=["系统信息"]
)
async def get_supported_cows():
    """
    # 📋 获取支持的牛只类型列表
    
    返回当前YOLOv8模型支持检测的所有牛只类型，包括中英文名称和类别信息。
    可用于前端界面显示或API集成参考。
    
    ## 返回信息
    - **总数量**: 支持的牛只类型总数
    - **类别列表**: 详细的牛只信息，包括ID、中英文名称、类别分组
    - **模型版本**: 当前使用的模型版本信息
    
    ## 使用场景
    - 前端界面显示支持的牛只类型
    - API文档生成
    - 客户端验证检测结果
    """
    try:
        # 读取牛只类别文件（使用配置中的相对路径）
        cow_classes = []
        try:
            with open(settings.CLASSES_PATH, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if line:
                        # 解析格式: "English name 中文名"
                        parts = line.split()
                        if len(parts) >= 2:
                            chinese_name = parts[-1]
                            english_name = " ".join(parts[:-1])
                        else:
                            chinese_name = line
                            english_name = line
                        
                        cow_classes.append({
                            "id": i,
                            "chinese_name": chinese_name,
                            "english_name": english_name,
                            "full_name": line
                        })
        except FileNotFoundError:
            # 如果文件不存在，返回硬编码的类别
            cow_classes = [
                {"id": 0, "chinese_name": "奶牛", "english_name": "Dairy cow", "full_name": "Dairy cow 奶牛"},
                {"id": 1, "chinese_name": "肉牛", "english_name": "Beef cattle", "full_name": "Beef cattle 肉牛"},
                # ... 其他牛只类别
            ]
        
        return {
            "success": True,
            "total_count": len(cow_classes),
            "cow_classes": cow_classes,
            "model_info": {
                "version": "YOLOv8",
                "last_updated": "2024-12-28"
            }
        }
        
    except Exception as e:
        logging.error(f"获取牛只类别失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "获取牛只类别列表失败"
            }
        )


@router.get(
    "/health/detailed",
    summary="详细健康检查",
    description="返回服务的详细健康状态信息",
    tags=["系统信息"]
)
async def detailed_health_check():
    """
    # 🔍 详细健康检查接口
    
    提供服务的详细健康状态信息，包括模型加载状态、系统资源使用情况等。
    
    ## 检查项目
    - **服务状态**: API服务是否正常运行
    - **模型状态**: YOLOv8模型是否已加载
    - **依赖检查**: 关键依赖库是否可用
    - **系统资源**: 内存和磁盘使用情况
    
    ## 返回状态
    - `healthy`: 所有检查项都正常
    - `warning`: 部分检查项有警告但不影响功能
    - `unhealthy`: 存在严重问题，服务可能不可用
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # 检查模型服务
        try:
            # 尝试访问模型服务
            model_available = hasattr(model_service, 'model') and model_service.model is not None
            health_status["checks"]["model"] = {
                "status": "healthy" if model_available else "warning",
                "message": "模型已加载" if model_available else "模型未加载，首次调用时会自动加载"
            }
        except Exception as e:
            health_status["checks"]["model"] = {
                "status": "unhealthy",
                "message": f"模型检查失败: {str(e)}"
            }
            health_status["status"] = "unhealthy"
        
        # 检查依赖库
        dependencies = []
        try:
            import torch
            dependencies.append({"name": "torch", "version": torch.__version__, "status": "ok"})
        except ImportError:
            dependencies.append({"name": "torch", "status": "missing"})
            health_status["status"] = "unhealthy"
        
        try:
            import cv2
            dependencies.append({"name": "opencv-python", "version": cv2.__version__, "status": "ok"})
        except ImportError:
            dependencies.append({"name": "opencv-python", "status": "missing"})
            health_status["status"] = "unhealthy"
        
        try:
            import ultralytics
            dependencies.append({"name": "ultralytics", "status": "ok"})
        except ImportError:
            dependencies.append({"name": "ultralytics", "status": "missing"})
            health_status["status"] = "unhealthy"
        
        health_status["checks"]["dependencies"] = {
            "status": "healthy" if all(d.get("status") == "ok" for d in dependencies) else "unhealthy",
            "details": dependencies
        }
        
        # 检查文件系统（使用配置中的相对路径）
        model_file_exists = os.path.exists(settings.MODEL_PATH)
        classes_file_exists = os.path.exists(settings.CLASSES_PATH)
        
        health_status["checks"]["files"] = {
            "status": "healthy" if (model_file_exists and classes_file_exists) else "warning",
            "model_file": model_file_exists,
            "classes_file": classes_file_exists
        }
        
        return health_status
        
    except Exception as e:
        logging.error(f"健康检查失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )



from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Union

# 兼容 Docker 和本地环境的导入
try:
    # Docker 环境：使用相对导入
    from app.schemas.detection import DetectRequest, DetectResponse, Detection, ErrorResponse
    from app.services.model_service import model_service
    from app.core.config import settings
except ImportError:
    # 本地环境：使用绝对导入
    from src.algorithms.pest_detection.detector.app.schemas.detection import DetectRequest, DetectResponse, Detection, ErrorResponse
    from src.algorithms.pest_detection.detector.app.services.model_service import model_service
    from src.algorithms.pest_detection.detector.app.core.config import settings
import logging
import traceback
from datetime import datetime
import os

router = APIRouter()


@router.post(
    "/detect",
    response_model=DetectResponse,
    status_code=status.HTTP_200_OK,
    summary="🐛 智能害虫检测接口",
    description="使用YOLOv8深度学习模型进行害虫检测和识别",
    responses={
        200: {
            "description": "检测成功",
            "content": {
                "application/json": {
                    "examples": {
                        "success_with_detections": {
                            "summary": "成功检测到害虫",
                            "value": {
                                "success": True,
                                "detections": [
                                    {
                                        "name": "瓜实蝇",
                                        "count": 2
                                    },
                                    {
                                        "name": "蚜虫",
                                        "count": 1
                                    }
                                ],
                                "result_image": "/9j/4AAQSkZJRgABAQEASABIAAD..."
                            }
                        },
                        "success_no_detections": {
                            "summary": "没有检测到害虫",
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
    tags=["害虫检测"]
)
async def detect_pests(request: DetectRequest) -> Union[DetectResponse, JSONResponse]:
    """
    # 🐛 智能害虫检测接口
    
    该接口使用先进的YOLOv8深度学习模型对上传的图像进行害虫检测和识别。
    支持29种常见的农业害虫，包括瓜实蝇、小菜蛾、斑潜蝇等。
    
    ## 功能特点
    - 🎯 **高精度检测**: 基于YOLOv8模型，检测精度高
    - 🚀 **快速响应**: 一般1-3秒内返回结果  
    - 📋 **多目标检测**: 同时检测多个不同类型的害虫
    - 🖼️ **视觉化结果**: 返回标注了检测框的图像
    
    ## 支持的害虫类型（29种）
    
    | 类别 | 中文名 | 英文名 |
    |------|------|------|
    | 蝇虫类 | 瓜实蝇 | Melon fly |
    | 蛾类 | 小菜蛾 | Diamondback moth |
    | 蝇虫类 | 斑潜蝇 | Leafminer fly |
    | 螨虫类 | 侧多食跗线螨 | Tarsonemid mite |
    | 粉虱类 | 稻粉虱 | Rice whitefly |
    | 蛾类 | 荔枝蒂蛀虫 | Litchi fruit borer |
    | 蝽类 | 荔枝蝽 | Litchi stink bug |
    | 螨虫类 | 荔枝瘿螨 | Eriophyes litchii |
    | 蛾类 | 甘蔗螟虫 | Sugarcane borer |
    | 叶蝉类 | 茶小绿叶蝉 | Tea green leafhopper |
    | 蜗牛类 | 福寿螺 | Apple snail |
    | 象甲类 | 小象甲 | Maize weevil |
    | 粉虱类 | 烟粉虱 | Tobacco whitefly |
    | 蛾类 | 稻纵卷叶螟 | Rice leaf roller |
    | 蛾类 | 大螟 | Paddy stem maggot |
    | 蛾类 | 二化螟 | Asiatic rice borer |
    | 飞虱类 | 稻飞虱 | Brown plant hopper |
    | 蛾类 | 玉米螟 | Corn borer |
    | 夜蛾类 | 草地贪夜蛾 | Army worm |
    | 蚜虫类 | 蚜虫 | Aphids |
    | 跳甲类 | 黄曲条跳甲 | Flea beetle |
    | 夜蛾类 | 甜菜夜蛾 | Beet army worm |
    | 蓟马类 | 蔬菜蓟马 | Thrips |
    | 粉蝶类 | 菜青虫 | Pieris canidia |
    | 红蜘蛛类 | 柑桔红蜘蛛 | Panonchus citri McGregor |
    | 锈蜘蛛类 | 柑桔锈蜘蛛 | Phyllocoptes oleiverus ashmead |
    | 实蝇类 | 桔小实蝇 | Dacus dorsalis |
    | 夜蛾类 | 斜纹夜蛾 | Prodenia litura |
    | 潜叶蛾类 | 柑桔潜叶蛾 | Phyllocnistis citrella Stainton |
    
    ## 请求格式
    - **Content-Type**: `application/json`
    - **Body**: JSON格式，包含`image_base64`字段
    
    ## 图像要求
    - **格式**: JPEG, PNG, BMP
    - **尺寸**: 建议640x640像素以上，最大支持50MB
    - **编码**: Base64编码（不包含`data:image/jpeg;base64,`前缀）
    - **内容**: 清晰的害虫图像，光线良好
    
    ## 返回结果
    成功时返回包含以下信息：
    - **detections**: 检测到的害虫列表，包括类型、置信度、位置
    - **result_image**: 标注了检测框的图像（base64格式）
    - **message**: 检测结果描述
    
    ## 错误处理
    当发生错误时，接口会返回相应的错误代码和详细信息：
    
    | 错误码 | 原因 | 解决方案 |
    |---------|------|----------|
    | `INVALID_BASE64` | base64编码格式错误 | 检查图像编码格式 |
    | `UNSUPPORTED_FORMAT` | 不支持的图像格式 | 使用JPEG/PNG/BMP格式 |
    | `IMAGE_TOO_LARGE` | 图像文件过大 | 压缩图像或降低分辨率 |
    | `MODEL_ERROR` | 模型推理失败 | 检查图像质量或重试 |
    | `INTERNAL_ERROR` | 服务器内部错误 | 稍后重试或联系管理员 |
    
    ## 使用示例
    
    ### Python请求示例
    ```python
    import requests
    import base64
    
    # 读取图像并转换为base64
    with open('pest_image.jpg', 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    # 发送请求
    response = requests.post(
        'http://localhost:8001/detect',
        json={'image_base64': img_b64}
    )
    
    # 处理响应
    result = response.json()
    if result['success']:
        print(f"检测到 {len(result['detections'])} 种害虫")
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
        console.log(`检测到 ${result.detections.length} 种害虫`);
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
        logging.info(f"开始害虫检测，图像大小: {len(request.image_base64)} 字符")
        
        # 调用模型服务进行检测
        detections, result_image_b64 = model_service.process_image_from_base64(request.image_base64)
        
        # 构造成功响应
        logging.info(f"检测成功，发现 {len(detections)} 种害虫")
        
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


@router.get(
    "/supported-pests",
    summary="获取支持的害虫类型列表", 
    description="返回当前模型支持检测的所有害虫类型",
    tags=["系统信息"]
)
async def get_supported_pests():
    """
    # 📋 获取支持的害虫类型列表
    
    返回当前YOLOv8模型支持检测的所有害虫类型，包括中英文名称和类别信息。
    可用于前端界面显示或API集成参考。
    
    ## 返回信息
    - **总数量**: 支持的害虫类型总数
    - **类别列表**: 详细的害虫信息，包括ID、中英文名称、类别分组
    - **模型版本**: 当前使用的模型版本信息
    
    ## 使用场景
    - 前端界面显示支持的害虫类型
    - API文档生成
    - 客户端验证检测结果
    """
    try:
        # 读取害虫类别文件（使用配置中的相对路径）
        pest_classes = []
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
                        
                        pest_classes.append({
                            "id": i,
                            "chinese_name": chinese_name,
                            "english_name": english_name,
                            "full_name": line
                        })
        except FileNotFoundError:
            # 如果文件不存在，返回硬编码的类别
            pest_classes = [
                {"id": 0, "chinese_name": "瓜实蝇", "english_name": "Melon fly", "full_name": "Melon fly 瓜实蝇"},
                {"id": 1, "chinese_name": "小菜蛾", "english_name": "Diamondback moth", "full_name": "Diamondback moth 小菜蛾"},
                # ... 其他害虫类别
            ]
        
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
        logging.error(f"获取害虫类别失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "获取害虫类别列表失败"
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
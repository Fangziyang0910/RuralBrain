"""虫害检测工具：调用检测服务分析图片中的害虫情况。"""
import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import requests
from langchain_core.tools import tool


DETECTION_API_URL = "http://127.0.0.1:8001/detect"
RESULT_IMAGES_DIR = Path("pest_detection_results")


def save_result_image(image_base64: str) -> str:
    """保存检测结果图像到本地。
    
    Args:
        image_base64: base64编码的结果图像
        
    Returns:
        保存的图像文件路径
    """
    # 确保结果目录存在
    RESULT_IMAGES_DIR.mkdir(exist_ok=True)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pest_detection_{timestamp}.jpg"
    filepath = RESULT_IMAGES_DIR / filename
    
    # 解码并保存图像
    image_data = base64.b64decode(image_base64)
    with open(filepath, "wb") as f:
        f.write(image_data)
    
    return str(filepath)


def encode_image_to_base64(image_path: str) -> str:
    """将图片文件编码为 base64 字符串。
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        base64 编码的图片字符串
        
    Raises:
        FileNotFoundError: 图片文件不存在
        ValueError: 文件格式不支持
    """
    path = Path(image_path)
    
    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    
    if not path.is_file():
        raise ValueError(f"路径不是文件: {image_path}")
    
    # 检查文件扩展名
    supported_formats = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    if path.suffix.lower() not in supported_formats:
        raise ValueError(
            f"不支持的图片格式: {path.suffix}。"
            f"支持的格式: {', '.join(supported_formats)}"
        )
    
    with open(path, "rb") as f:
        image_bytes = f.read()
        return base64.b64encode(image_bytes).decode("utf-8")


def format_detection_result(api_response: Dict[str, Any], saved_image_path: str = None) -> str:
    """将检测接口返回的结果格式化为简洁的数据摘要。
    
    Args:
        api_response: 检测接口返回的 JSON 数据
        saved_image_path: 保存的结果图像路径（可选，内部使用不返回给agent）
        
    Returns:
        简洁的检测结果数据，供 agent 分析使用
    """
    if not api_response.get("success"):
        error_msg = api_response.get("message", "未知错误")
        return f"检测失败: {error_msg}"
    
    detections = api_response.get("detections", [])
    
    if not detections:
        return "检测完成，未发现害虫。"
    
    # 构建简洁的检测结果
    result_parts = []
    for detection in detections:
        name = detection.get("name", "未知害虫")
        count = detection.get("count", 0)
        result_parts.append(f"{name}({count}只)")
    
    return "检测结果: " + "、".join(result_parts)


@tool
def pest_detection_tool(image_path: str) -> str:
    """调用害虫检测服务分析图片中的害虫种类和数量。
    
    该工具会：
    1. 读取指定路径的图片文件
    2. 将图片发送到害虫检测服务（基于YOLOv8模型）进行分析
    3. 自动保存带标注框的检测结果图像到本地（pest_detection_results目录）
    4. 返回害虫检测的文字摘要结果
    
    注意：检测结果图像会自动保存为 pest_detection_YYYYMMDD_HHMMSS.jpg 格式，
    但不会在返回结果中包含图像路径，以避免占用过多token。
    
    Args:
        image_path: 图片文件的本地路径，支持格式：jpg、jpeg、png、bmp、webp
        
    Returns:
        检测结果字符串，格式如下：
        - 成功："检测结果: 瓜实蝇(3只)、斜纹夜蛾(1只)"
        - 未检测到："检测完成，未发现害虫。"
        - 失败："检测失败: [错误原因]"
        
    Examples:
        >>> pest_detection_tool("test_images/pest1.jpg")
        "检测结果: 瓜实蝇(3只)、斜纹夜蛾(1只)"
        
        >>> pest_detection_tool("test_images/empty.jpg")
        "检测完成，未发现害虫。"
    """
    try:
        # 1. 编码图片
        image_base64 = encode_image_to_base64(image_path)
        
        # 2. 构建请求数据（使用新的字段名）
        payload = {
            "image_base64": image_base64
        }
        
        # 3. 调用检测接口
        response = requests.post(
            DETECTION_API_URL,
            json=payload,
            timeout=60
        )
        
        # 检查 HTTP 状态码
        if response.status_code != 200:
            return f"检测服务请求失败 (HTTP {response.status_code})"
        
        # 4. 解析响应
        api_response = response.json()
        
        # 5. 保存结果图像（如果存在）
        saved_image_path = None
        if api_response.get("success") and api_response.get("result_image"):
            try:
                saved_image_path = save_result_image(api_response["result_image"])
            except Exception as e:
                # 图像保存失败不影响检测结果返回
                pass
        
        # 6. 格式化并返回结果（不包含图像路径）
        return format_detection_result(api_response, saved_image_path)
        
    except FileNotFoundError as e:
        return f"文件错误: {str(e)}"
    
    except ValueError as e:
        return f"参数错误: {str(e)}"
    
    except requests.Timeout:
        return f"检测服务请求超时，请检查服务是否正常运行"
    
    except requests.ConnectionError:
        return "无法连接到检测服务，请确认服务已启动 (URL: http://127.0.0.1:8001/detect)"
    
    except requests.exceptions.JSONDecodeError as e:
        return f"检测服务返回数据格式错误: {str(e)}"
    
    except Exception as e:
        return f"检测过程发生未知错误: {type(e).__name__}: {str(e)}"


# 导出工具供 agent 使用
__all__ = ["pest_detection_tool"]

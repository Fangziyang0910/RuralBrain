"""虫害检测工具：调用检测服务分析图片中的害虫情况。"""
import base64
import json
import uuid
from pathlib import Path
from typing import Any, Dict
import requests
from langchain_core.tools import tool


DETECTION_API_URL = "http://127.0.0.1:8000/detect"


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


def format_detection_result(api_response: Dict[str, Any]) -> str:
    """将检测接口返回的结果格式化为简洁的数据摘要。
    
    Args:
        api_response: 检测接口返回的 JSON 数据
        
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
    """调用虫害检测服务分析图片中的害虫情况。
    
    该工具会读取指定路径的图片文件，将其发送到虫害检测服务进行分析，
    并返回识别到的害虫种类和数量的简洁数据。
    
    Args:
        image_path: 图片文件的本地路径（支持 jpg、png、bmp、webp 格式）
        
    Returns:
        简洁的检测结果数据，例如："检测结果: 瓜实蝇(3只)、斜纹夜蛾(1只)"
    """
    try:
        # 1. 编码图片
        image_base64 = encode_image_to_base64(image_path)
        
        # 2. 构建请求数据（包含 session_id）
        session_id = str(uuid.uuid4())
        payload = {
            "session_id": session_id,
            "image": image_base64
        }
        
        # 3. 调用检测接口（静默执行，不打印调试信息）
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
        
        # 5. 格式化并返回结果
        return format_detection_result(api_response)
        
    except FileNotFoundError as e:
        return f"文件错误: {str(e)}"
    
    except ValueError as e:
        return f"参数错误: {str(e)}"
    
    except requests.Timeout:
        return f"检测服务请求超时，请检查服务是否正常运行"
    
    except requests.ConnectionError:
        return f"无法连接到检测服务，请确认服务已启动"
    
    except json.JSONDecodeError as e:
        return f"检测服务返回数据格式错误: {str(e)}"
    
    except Exception as e:
        return f"检测过程发生未知错误: {type(e).__name__}: {str(e)}"


# 导出工具供 agent 使用
__all__ = ["pest_detection_tool"]

"""大米品种识别工具。

调用大米识别服务分析图片中的大米品种。
"""
from pathlib import Path
from typing import Any
import uuid

import requests
from langchain_core.tools import tool

from .detection_utils import encode_image_to_base64, save_result_image


API_URL = "http://127.0.0.1:8081/predict"
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def validate_image_path(image_path: str) -> None:
    """验证图片路径是否有效。

    Args:
        image_path: 图片文件路径

    Raises:
        FileNotFoundError: 图片文件不存在
        ValueError: 文件格式不支持
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {image_path}")

    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"不支持的图片格式: {path.suffix}。"
            f"支持的格式: {', '.join(SUPPORTED_FORMATS)}"
        )


def encode_image_to_base64_with_validation(image_path: str) -> str:
    """编码图片为 base64 并进行验证。

    Args:
        image_path: 图片文件路径

    Returns:
        base64 编码的图片字符串
    """
    validate_image_path(image_path)
    return encode_image_to_base64(image_path)


def save_result_image_base64(image_base64: str) -> str:
    """保存检测结果图像到本地。

    Args:
        image_base64: base64 编码的结果图像

    Returns:
        保存的图像文件绝对路径
    """
    import base64

    image_data = base64.b64decode(image_base64)
    return save_result_image(image_data, "rice_detection_results", "rice_detection")


def format_detection_result(api_response: dict[str, Any]) -> str:
    """将检测接口返回的结果格式化为简洁的数据摘要。

    Args:
        api_response: 检测接口返回的 JSON 数据

    Returns:
        简洁的检测结果字符串
    """
    if not api_response.get("success"):
        return f"识别服务报错: {api_response.get('message', '未知错误')}"

    detections = api_response.get("detections", [])

    if not detections:
        return "识别完成，但在图片中未检测到明显的大米颗粒。"

    summary = []
    for item in detections:
        name = item.get("name", "未知品种")
        count = item.get("count", 0)
        summary.append(f"{name}({count}粒)")

    return "识别成功。检测结果: " + "、".join(summary)


@tool
def rice_detection_tool(image_path: str, task_type: str = "品种分类") -> str:
    """调用大米识别服务分析图片中的大米品种。

    该工具会：
    1. 读取指定路径的图片文件
    2. 将图片发送到大米识别服务进行分析
    3. 自动保存带标注框的检测结果图像到本地（rice_detection_results 目录）
    4. 返回大米品种识别的文字摘要结果

    注意：检测结果图像会自动保存，但不会在返回结果中包含图像路径，
    以避免占用过多 token。

    Args:
        image_path: 图片文件的本地路径，支持格式：jpg、jpeg、png、bmp、webp
        task_type: 任务类型，默认为"品种分类"

    Returns:
        识别结果的文字摘要，示例：
        - 成功："识别成功。检测结果: 丝苗米(25粒)、珍珠米(18粒)"
        - 未检测到："识别完成，但在图片中未检测到明显的大米颗粒。"
        - 失败："识别服务报错: [错误原因]"

    Examples:
        >>> rice_detection_tool("test_images/rice1.jpg")
        "识别成功。检测结果: 丝苗米(25粒)、珍珠米(18粒)"
    """
    try:
        img_base64 = encode_image_to_base64_with_validation(image_path)
        payload = {
            "image_base64": img_base64,
            "task_type": task_type,
            "session_id": str(uuid.uuid4())
        }

        response = requests.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        response.raise_for_status()

        api_response = response.json()

        if api_response.get("success") and api_response.get("result_image"):
            try:
                save_result_image_base64(api_response["result_image"])
            except Exception:
                pass

        return format_detection_result(api_response)

    except FileNotFoundError as e:
        return f"文件错误: {str(e)}"
    except ValueError as e:
        return f"参数错误: {str(e)}"
    except requests.Timeout:
        return "识别服务请求超时，请检查服务是否正常运行"
    except requests.ConnectionError:
        return "无法连接到识别服务，请确认服务已启动"
    except requests.exceptions.JSONDecodeError as e:
        return f"识别服务返回数据格式错误: {str(e)}"
    except requests.HTTPError as e:
        return f"识别服务请求失败: {str(e)}"
    except Exception as e:
        return f"工具调用过程发生错误: {type(e).__name__}: {str(e)}"


__all__ = ["rice_detection_tool"]
rice_detection_tool.tags = ["detection", "rice"]

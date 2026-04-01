"""大米品种识别工具。

调用大米识别服务分析图片中的大米品种。
支持多模态和非多模态模型：
- 多模态模型：自动从消息历史中提取 base64 图片
- 非多模态模型：自动从消息历史中提取图片路径
"""
from pathlib import Path
import os
from typing import Any
import uuid
import logging

import requests
from langchain_core.tools import tool
from langchain.tools import ToolRuntime

from .detection_utils import (
    encode_image_to_base64,
    save_result_image,
    extract_image_from_messages,
    generate_detection_explanation,
)

logger = logging.getLogger(__name__)


API_URL = os.getenv(
    "RICE_DETECTION_API_URL",
    "http://detection-service:8001/detection/rice/predict"
)
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


def save_result_image_base64(image_base64: str) -> str:
    """保存检测结果图像到本地。

    Args:
        image_base64: base64 编码的结果图像

    Returns:
        保存的图像文件访问路径
    """
    import base64

    image_data = base64.b64decode(image_base64)
    return save_result_image(image_data, "rice", "rice_detection")


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
def rice_detection_tool(runtime: ToolRuntime) -> str:
    """调用大米识别服务分析用户上传图片中的大米品种。

    自动从对话历史中提取用户上传的图片，无需手动传递图片路径。
    支持多模态模型（base64 图片）和非多模态模型（图片路径）。

    Returns:
        识别结果的文字摘要，示例：
        - 成功："识别成功。检测结果: 丝苗米(25粒)、珍珠米(18粒)"
        - 未检测到："识别完成，但在图片中未检测到明显的大米颗粒。"
        - 未找到图片："未找到图片信息，请先上传图片"
        - 失败："识别服务报错: [错误原因]"
    """
    try:
        # 从消息历史中提取图片信息
        messages = runtime.state["messages"]
        image_info = extract_image_from_messages(messages)

        if image_info is None:
            return "未找到图片信息，请先上传图片后再进行识别。"

        # 获取 base64 数据（多模态格式直接提供，路径格式需要编码）
        if "base64" in image_info:
            image_base64 = image_info["base64"]
            logger.info("使用多模态消息中的 base64 图片进行识别")
        else:
            image_path = image_info["path"]
            # 验证路径
            validate_image_path(image_path)
            image_base64 = encode_image_to_base64(image_path)
            logger.info(f"使用图片路径进行识别: {image_path}")

        payload = {
            "image_base64": image_base64,
            "task_type": "品种分类",
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

        # 生成基础检测结果
        base_result = format_detection_result(api_response)

        # 获取模型 ID（用于判断是否支持多模态）
        model_id = ""
        if runtime.context:
            model_id = getattr(runtime.context, "model_id", "")

        # 调用解释层生成智能分析
        explanation = generate_detection_explanation(
            detection_type="rice",
            detection_result=api_response,
            image_base64=image_base64,
            model_id=model_id
        )

        # 合并输出
        if explanation:
            return f"{base_result}\n\n---\n\n{explanation}"
        return base_result

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
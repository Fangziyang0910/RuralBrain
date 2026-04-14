"""奶牛检测工具。

调用奶牛检测服务分析图片中的奶牛种类和数量。
支持多模态和非多模态模型：
- 多模态模型：自动从消息历史中提取 base64 图片
- 非多模态模型：自动从消息历史中提取图片路径

增强版本：返回详细检测数据（边界框、置信度），供前端可视化展示。
"""
from pathlib import Path
import os
from typing import Any
import logging
import json

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


# 基础检测 API URL
DETECTION_API_URL = os.getenv(
    "COW_DETECTION_API_URL",
    "http://detection-service:8001/detection/cow/detect"
)
# 详细检测 API URL（新增）
DETECTION_API_URL_DETAILED = os.getenv(
    "COW_DETECTION_API_URL_DETAILED",
    "http://detection-service:8001/detection/cow/detect_detailed"
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
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    if not path.is_file():
        raise ValueError(f"路径不是文件: {image_path}")

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
    return save_result_image(image_data, "cow", "cow_detection")


def format_detection_result(api_response: dict[str, Any]) -> str:
    """将检测接口返回的结果格式化为简洁的数据摘要。

    Args:
        api_response: 检测接口返回的 JSON 数据

    Returns:
        简洁的检测结果字符串
    """
    if not api_response.get("success"):
        error_msg = api_response.get("error", api_response.get("message", "未知错误"))
        return f"检测失败: {error_msg}"

    detections = api_response.get("detections", [])

    if not detections:
        return "检测完成，未发现奶牛。"

    result_parts = []
    total_count = 0
    for detection in detections:
        name = detection.get("name", "未知品种")
        count = detection.get("count", 0)
        total_count += count
        result_parts.append(f"{name}({count}只)")

    summary = "、".join(result_parts)
    return f"检测结果: {summary}，共计{total_count}只奶牛"


def build_enhanced_output(
    base_result: str,
    api_response: dict[str, Any],
    explanation: str | None = None
) -> str:
    """构建增强输出，包含文本摘要和详细数据。

    输出格式为 JSON 字符串，包含：
    - text: 用于 Agent 理解的文本摘要
    - data: 详细检测数据（供前端可视化）

    Args:
        base_result: 基础检测结果文本
        api_response: API 返回的完整响应
        explanation: LLM 生成的解释文本

    Returns:
        JSON 格式的增强输出字符串
    """
    # 提取详细检测数据
    detailed_detections = api_response.get("detailed_detections", [])
    image_info = api_response.get("image_info", {})

    # 计算平均置信度
    avg_confidence = 0.0
    if detailed_detections:
        confidences = [d.get("confidence", 0) for d in detailed_detections]
        avg_confidence = sum(confidences) / len(confidences)

    # 判断严重程度
    severity = "none"
    if detailed_detections:
        if avg_confidence >= 0.8:
            severity = "low"  # 高置信度 = 确定检测，问题不大
        elif avg_confidence >= 0.5:
            severity = "medium"
        else:
            severity = "high"  # 低置信度 = 可能误检

    # 构建输出数据
    output = {
        "text": base_result,  # Agent 用于理解的文本
        "data": {
            "detections": api_response.get("detections", []),
            "totalCount": image_info.get("total_cows", 0),
            "severity": severity,
            "summary": base_result.split("\n")[0] if base_result else "",
            "detailed_detections": detailed_detections,
            "image_info": image_info,
            "avg_confidence": avg_confidence,
        }
    }

    # 添加 LLM 解释（如果有）
    if explanation:
        output["text"] = f"{base_result}\n\n---\n\n{explanation}"

    return json.dumps(output, ensure_ascii=False)


@tool
def cow_detection_tool(runtime: ToolRuntime) -> str:
    """调用奶牛检测服务分析用户上传图片中的奶牛数量。

    自动从对话历史中提取用户上传的图片，无需手动传递图片路径。
    支持多模态模型（base64 图片）和非多模态模型（图片路径）。

    **增强版本**: 返回详细检测数据（边界框、置信度），供前端可视化展示。

    Returns:
        JSON 格式的检测结果，包含：
        - text: 用于 Agent 理解的文本摘要
        - data: 详细检测数据（供前端可视化）

        示例：
        - 成功：{"text": "检测结果: cow(5只)...", "data": {...}}
        - 未检测到：{"text": "检测完成，未发现奶牛。", "data": {...}}
        - 未找到图片：未找到图片信息，请先上传图片后再进行检测。
        - 失败：检测失败: [错误原因]
    """
    try:
        # 从消息历史中提取图片信息
        messages = runtime.state["messages"]
        image_info = extract_image_from_messages(messages)

        if image_info is None:
            return "未找到图片信息，请先上传图片后再进行检测。"

        # 获取 base64 数据（多模态格式直接提供，路径格式需要编码）
        if "base64" in image_info:
            image_base64 = image_info["base64"]
            logger.info("使用多模态消息中的 base64 图片进行检测")
        else:
            image_path = image_info["path"]
            # 验证路径
            validate_image_path(image_path)
            image_base64 = encode_image_to_base64(image_path)
            logger.info(f"使用图片路径进行检测: {image_path}")

        payload = {"image_base64": image_base64}

        # 调用详细检测 API（获取 bbox 和 confidence）
        response = requests.post(
            DETECTION_API_URL_DETAILED,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            return f"检测服务请求失败 (HTTP {response.status_code})"

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
            detection_type="cow",
            detection_result=api_response,
            image_base64=image_base64,
            model_id=model_id
        )

        # 构建增强输出（JSON 格式）
        return build_enhanced_output(base_result, api_response, explanation)

    except FileNotFoundError as e:
        return f"文件错误: {str(e)}"
    except ValueError as e:
        return f"参数错误: {str(e)}"
    except requests.Timeout:
        return "检测服务请求超时，请检查服务是否正常运行"
    except requests.ConnectionError:
        return "无法连接到检测服务，请确认服务已启动"
    except requests.exceptions.JSONDecodeError as e:
        return f"检测服务返回数据格式错误: {str(e)}"
    except Exception as e:
        return f"检测过程发生未知错误: {type(e).__name__}: {str(e)}"


__all__ = ["cow_detection_tool"]
cow_detection_tool.tags = ["detection", "cow"]
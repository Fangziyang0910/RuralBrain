"""检测工具共享模块。

提供图像检测工具的通用辅助函数，包括结果保存、编码和格式化。
"""
import base64
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any
import uuid

from langchain_core.messages import HumanMessage

from service.settings import DETECTION_RESULTS_DIR, MAX_CACHE_SIZE
from src.utils.file_manager import cleanup_lru

logger = logging.getLogger(__name__)


def save_result_image(
    image_content: bytes,
    detection_type: str,
    file_prefix: str,
) -> str:
    """保存检测结果图片（带自动 LRU 清理）

    Args:
        image_content: 图片二进制内容
        detection_type: 检测类型（pest/cow/rice）
        file_prefix: 结果文件名前缀

    Returns:
        图片访问路径（URL 路径）
    """
    # 1. 确定保存目录
    results_dir = DETECTION_RESULTS_DIR / detection_type
    results_dir.mkdir(exist_ok=True)

    # 2. 检查并清理（如果容量超限）
    cleanup_lru(DETECTION_RESULTS_DIR, MAX_CACHE_SIZE)

    # 3. 保存新文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{file_prefix}_result_{timestamp}_{unique_id}.jpg"
    file_path = results_dir / filename
    file_path.write_bytes(image_content)

    # 4. 返回访问路径
    return f"/{detection_type}_results/{filename}"


def encode_image_to_base64(image_path: str) -> str:
    """将图片文件编码为 base64 字符串。

    Args:
        image_path: 图片文件路径

    Returns:
        base64 编码的图片字符串
    """
    image_bytes = Path(image_path).read_bytes()
    return base64.b64encode(image_bytes).decode("utf-8")


def format_detection_result(
    success: bool,
    data: dict[str, Any] | None = None,
    error: str | None = None,
) -> str:
    """格式化检测结果为 JSON 字符串。

    Args:
        success: 操作是否成功
        data: 成功时的结果数据
        error: 失败时的错误信息

    Returns:
        JSON 格式的结果字符串
    """
    result: dict[str, Any] = {"success": success}

    if success:
        if data:
            result.update(data)
    else:
        result["error"] = error or "未知错误"

    return json.dumps(result, ensure_ascii=False)


def extract_image_from_messages(messages: list) -> dict | None:
    """从消息历史中提取图片信息。

    支持两种消息格式：
    - 多模态消息：从 content blocks 中提取 base64 图片数据
    - 纯文本消息：从文本中提取图片路径（[图片路径 N: /path] 格式）

    Args:
        messages: LangChain 消息历史列表

    Returns:
        包含图片信息的字典：
        - {"base64": str, "mime_type": str} - 多模态格式
        - {"path": str} - 路径格式
        - None - 未找到图片
    """
    for message in reversed(messages):
        if not isinstance(message, HumanMessage):
            continue

        content = message.content

        # 多模态消息格式（列表形式）
        if isinstance(content, list):
            for block in content:
                # LangChain 标准 image block 格式
                if block.get("type") == "image":
                    base64_data = block.get("base64")
                    if base64_data:
                        logger.info("从多模态消息中提取到 base64 图片")
                        return {
                            "base64": base64_data,
                            "mime_type": block.get("mime_type", "image/jpeg"),
                        }

                # OpenAI 兼容格式 (image_url)
                elif block.get("type") == "image_url":
                    image_url = block.get("image_url", {})
                    url = image_url.get("url", "")
                    # data:image/jpeg;base64,<data>
                    if url.startswith("data:"):
                        match = re.match(r"data:(.+);base64,(.+)", url)
                        if match:
                            mime_type, base64_data = match.groups()
                            logger.info("从 OpenAI 兼容格式中提取到 base64 图片")
                            return {
                                "base64": base64_data,
                                "mime_type": mime_type,
                            }

        # 纯文本消息格式（从中提取路径）
        elif isinstance(content, str):
            # 匹配 [图片路径 N: /path] 格式
            match = re.search(r"\[图片路径\s*\d*:\s*(.+?)\]", content)
            if match:
                path = match.group(1).strip()
                logger.info(f"从文本消息中提取到图片路径: {path}")
                return {"path": path}

    logger.warning("未从消息历史中找到图片信息")
    return None


__all__ = [
    "save_result_image",
    "encode_image_to_base64",
    "format_detection_result",
    "extract_image_from_messages",
]

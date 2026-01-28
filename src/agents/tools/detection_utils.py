"""检测工具共享模块。

提供图像检测工具的通用辅助函数，包括结果保存、编码和格式化。
"""
import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any
import uuid


def save_result_image(
    image_content: bytes,
    directory_name: str,
    file_prefix: str,
) -> str:
    """保存检测结果图片到指定目录。

    Args:
        image_content: 图片二进制内容
        directory_name: 结果保存目录名称
        file_prefix: 结果文件名前缀

    Returns:
        保存的图片文件绝对路径
    """
    results_dir = Path(directory_name)
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{file_prefix}_result_{timestamp}_{unique_id}.jpg"
    file_path = results_dir / filename

    file_path.write_bytes(image_content)
    return str(file_path.absolute())


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

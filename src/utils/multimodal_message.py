"""多模态消息构建工具

将图片编码为 base64 并构建 LangChain 多模态消息格式。
"""
import logging
import mimetypes
from typing import List, Optional

from langchain_core.messages import HumanMessage

from src.config import AVAILABLE_MODELS
from src.agents.tools.detection_utils import encode_image_to_base64

logger = logging.getLogger(__name__)


def build_multimodal_message(
    text: str,
    image_paths: Optional[List[str]] = None,
    model_id: Optional[str] = None,
) -> HumanMessage:
    """
    构建多模态 HumanMessage

    根据模型是否支持多模态，自动选择消息格式：
    - 支持多模态：构建结构化消息（文本 + base64 图片）
    - 不支持多模态：构建纯文本消息（附带图片路径提示）

    Args:
        text: 用户文本消息
        image_paths: 图片路径列表
        model_id: 当前使用的模型ID，用于判断是否支持多模态

    Returns:
        HumanMessage: 多模态消息（如果模型支持）或纯文本消息
    """
    # 没有图片，返回纯文本消息
    if not image_paths:
        return HumanMessage(content=text)

    # 判断当前模型是否支持多模态
    model_config = AVAILABLE_MODELS.get(model_id, {})
    is_multimodal = model_config.get("is_multimodal", False)

    if not is_multimodal:
        # 不支持多模态，使用文本格式（附带路径提示）
        paths_text = "\n".join(
            [f"[图片路径 {i+1}: {path}]" for i, path in enumerate(image_paths)]
        )
        logger.info(f"模型 {model_id} 不支持多模态，使用文本格式传递图片路径")
        return HumanMessage(content=f"{text}\n\n{paths_text}")

    # 支持多模态，构建结构化消息
    content_blocks: List[dict] = [{"type": "text", "text": text}]

    for image_path in image_paths:
        try:
            # 获取 MIME 类型
            mime_type, _ = mimetypes.guess_type(image_path)
            if mime_type is None:
                mime_type = "image/jpeg"

            # 编码图片为 base64
            image_base64 = encode_image_to_base64(image_path)

            # 使用 OpenAI 兼容格式（Qwen3.6-Plus 支持）
            content_blocks.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{image_base64}"
                }
            })

            logger.info(f"图片已编码为 base64: {image_path} ({mime_type})")

        except Exception as e:
            logger.error(f"图片编码失败: {image_path}, 错误: {e}")
            # 降级处理：在文本中添加图片路径提示
            content_blocks[0]["text"] += f"\n\n[图片读取失败: {image_path}]"

    logger.info(f"构建多模态消息: 文本长度={len(text)}, 图片数量={len(content_blocks) - 1}")
    return HumanMessage(content=content_blocks)


def is_model_multimodal(model_id: Optional[str]) -> bool:
    """
    判断指定模型是否支持多模态

    Args:
        model_id: 模型ID

    Returns:
        bool: 是否支持多模态
    """
    if not model_id:
        return False
    return AVAILABLE_MODELS.get(model_id, {}).get("is_multimodal", False)
"""
多模态消息构建工具

提供便捷的方法构建包含图片的多模态消息，用于 Qwen3.5-Plus 等视觉语言模型。
Qwen3.5-Plus 原生支持多模态，可处理图片+文本的输入。
"""
import base64
import mimetypes
from pathlib import Path
from typing import List, Optional, Union

from langchain_core.messages import HumanMessage


class MultimodalHelper:
    """
    多模态消息构建工具类

    用于构建包含图片和文本的 HumanMessage，支持：
    - 本地图片文件（自动读取并转为 base64）
    - 图片 URL（直接传递）
    - Base64 编码的图片数据

    Example:
        >>> from src.utils.multimodal import MultimodalHelper
        >>>
        >>> # 从本地文件构建消息
        >>> message = MultimodalHelper.build_image_message(
        ...     text="描述这张图片",
        ...     image_path="/path/to/image.jpg"
        ... )
        >>>
        >>> # 从 URL 构建消息
        >>> message = MultimodalHelper.build_image_message(
        ...     text="分析这张图片的内容",
        ...     image_url="https://example.com/image.jpg"
        ... )
        >>>
        >>> # 多图片消息
        >>> message = MultimodalHelper.build_multi_image_message(
        ...     text="比较这些图片",
        ...     image_paths=["/path/to/img1.jpg", "/path/to/img2.jpg"]
        ... )
    """

    @staticmethod
    def encode_image_to_base64(image_path: Union[str, Path]) -> tuple[str, str]:
        """
        将图片文件编码为 base64 字符串

        Args:
            image_path: 图片文件路径

        Returns:
            (base64_string, mime_type): base64 编码的图片数据和 MIME 类型

        Raises:
            FileNotFoundError: 图片文件不存在
            ValueError: 不支持的图片格式
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {path}")

        # 获取 MIME 类型
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type or not mime_type.startswith("image/"):
            # 根据扩展名推断
            suffix = path.suffix.lower()
            mime_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
                ".bmp": "image/bmp",
            }
            mime_type = mime_map.get(suffix, "image/jpeg")

        # 读取并编码
        with open(path, "rb") as f:
            image_data = f.read()

        base64_str = base64.b64encode(image_data).decode("utf-8")
        return base64_str, mime_type

    @staticmethod
    def build_image_content(
        image_path: Optional[Union[str, Path]] = None,
        image_url: Optional[str] = None,
        base64_data: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> dict:
        """
        构建单个图片内容块

        Args:
            image_path: 本地图片路径（优先）
            image_url: 图片 URL
            base64_data: Base64 编码的图片数据
            mime_type: MIME 类型（使用 base64_data 时需要）

        Returns:
            图片内容块字典

        Example:
            >>> content = MultimodalHelper.build_image_content(image_path="/path/to/img.jpg")
            >>> # {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        """
        if image_path:
            b64_data, detected_mime = MultimodalHelper.encode_image_to_base64(image_path)
            url = f"data:{detected_mime};base64,{b64_data}"
        elif image_url:
            url = image_url
        elif base64_data:
            if not mime_type:
                mime_type = "image/jpeg"  # 默认
            url = f"data:{mime_type};base64,{base64_data}"
        else:
            raise ValueError("必须提供 image_path、image_url 或 base64_data 其中之一")

        return {
            "type": "image_url",
            "image_url": {"url": url}
        }

    @staticmethod
    def build_image_message(
        text: str,
        image_path: Optional[Union[str, Path]] = None,
        image_url: Optional[str] = None,
        base64_data: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> HumanMessage:
        """
        构建包含单张图片的 HumanMessage

        Args:
            text: 文本提示
            image_path: 本地图片路径（优先）
            image_url: 图片 URL
            base64_data: Base64 编码的图片数据
            mime_type: MIME 类型

        Returns:
            HumanMessage: 包含图片和文本的消息

        Example:
            >>> message = MultimodalHelper.build_image_message(
            ...     text="这张图片里有什么？",
            ...     image_path="/path/to/image.jpg"
            ... )
        """
        content = [
            {"type": "text", "text": text},
            MultimodalHelper.build_image_content(
                image_path=image_path,
                image_url=image_url,
                base64_data=base64_data,
                mime_type=mime_type,
            )
        ]
        return HumanMessage(content=content)

    @staticmethod
    def build_multi_image_message(
        text: str,
        image_paths: Optional[List[Union[str, Path]]] = None,
        image_urls: Optional[List[str]] = None,
    ) -> HumanMessage:
        """
        构建包含多张图片的 HumanMessage

        Args:
            text: 文本提示
            image_paths: 本地图片路径列表
            image_urls: 图片 URL 列表

        Returns:
            HumanMessage: 包含多张图片和文本的消息

        Example:
            >>> message = MultimodalHelper.build_multi_image_message(
            ...     text="比较这两张图片的差异",
            ...     image_paths=["/path/to/img1.jpg", "/path/to/img2.jpg"]
            ... )
        """
        content = [{"type": "text", "text": text}]

        if image_paths:
            for path in image_paths:
                content.append(MultimodalHelper.build_image_content(image_path=path))

        if image_urls:
            for url in image_urls:
                content.append(MultimodalHelper.build_image_content(image_url=url))

        return HumanMessage(content=content)


__all__ = ["MultimodalHelper"]
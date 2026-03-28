"""
测试多模态消息构建工具

验证 build_multimodal_message 函数的核心行为：
1. 没有图片时返回纯文本消息
2. is_multimodal=False 时在纯文本里附加 [图片路径 N: ...]
3. is_multimodal=True 时生成 [{type:text},{type:image_url,...}] blocks
4. 编码异常时降级处理并返回可用的 HumanMessage
5. MIME 类型推断逻辑

验证 extract_image_from_messages 函数的核心行为：
1. OpenAI 兼容 image_url data URL 的解析
2. 文本路径格式解析
3. 反向遍历时取到"最近一条"含图片的 HumanMessage
4. 未找到图片时返回 None
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from langchain_core.messages import HumanMessage, AIMessage
from src.utils.multimodal_message import build_multimodal_message, is_model_multimodal
from src.agents.tools.detection_utils import extract_image_from_messages


class TestBuildMultimodalMessage:
    """测试 build_multimodal_message 函数"""

    def test_no_image_returns_pure_text(self):
        """测试：没有图片时返回纯文本 HumanMessage"""
        result = build_multimodal_message("你好", image_paths=None, model_id="qwen")

        assert isinstance(result, HumanMessage)
        assert result.content == "你好"

    def test_no_image_with_empty_list_returns_pure_text(self):
        """测试：图片列表为空时返回纯文本 HumanMessage"""
        result = build_multimodal_message("你好", image_paths=[], model_id="qwen")

        assert isinstance(result, HumanMessage)
        assert result.content == "你好"

    def test_non_multimodal_model_appends_image_paths(self):
        """测试：is_multimodal=False 时在文本中附加图片路径"""
        # Mock AVAILABLE_MODELS 返回非多模态模型配置
        mock_models = {
            "deepseek": {"is_multimodal": False}
        }

        with patch("src.utils.multimodal_message.AVAILABLE_MODELS", mock_models):
            result = build_multimodal_message(
                "请检测这张图片",
                image_paths=["/path/to/image1.jpg", "/path/to/image2.png"],
                model_id="deepseek"
            )

        assert isinstance(result, HumanMessage)
        assert isinstance(result.content, str)
        assert "请检测这张图片" in result.content
        assert "[图片路径 1: /path/to/image1.jpg]" in result.content
        assert "[图片路径 2: /path/to/image2.png]" in result.content

    def test_multimodal_model_generates_content_blocks(self):
        """测试：is_multimodal=True 时生成结构化消息 blocks"""
        mock_models = {
            "qwen": {"is_multimodal": True}
        }
        mock_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"

        with patch("src.utils.multimodal_message.AVAILABLE_MODELS", mock_models):
            with patch("src.utils.multimodal_message.encode_image_to_base64", return_value=mock_base64):
                result = build_multimodal_message(
                    "请分析这张图片",
                    image_paths=["/path/to/test.jpg"],
                    model_id="qwen"
                )

        assert isinstance(result, HumanMessage)
        assert isinstance(result.content, list)
        assert len(result.content) == 2  # 1 text + 1 image

        # 验证文本 block
        text_block = result.content[0]
        assert text_block["type"] == "text"
        assert text_block["text"] == "请分析这张图片"

        # 验证图片 block (OpenAI 兼容格式)
        image_block = result.content[1]
        assert image_block["type"] == "image_url"
        assert "image_url" in image_block
        assert image_block["image_url"]["url"].startswith("data:image/jpeg;base64,")
        assert mock_base64 in image_block["image_url"]["url"]

    def test_multimodal_model_with_multiple_images(self):
        """测试：多图片场景生成多个 image_url blocks"""
        mock_models = {
            "qwen": {"is_multimodal": True}
        }
        mock_base64_1 = "base64data1"
        mock_base64_2 = "base64data2"

        with patch("src.utils.multimodal_message.AVAILABLE_MODELS", mock_models):
            with patch("src.utils.multimodal_message.encode_image_to_base64", side_effect=[mock_base64_1, mock_base64_2]):
                result = build_multimodal_message(
                    "请对比这两张图片",
                    image_paths=["/path/a.jpg", "/path/b.png"],
                    model_id="qwen"
                )

        assert isinstance(result.content, list)
        assert len(result.content) == 3  # 1 text + 2 images

        # 验证所有图片 block 都存在
        image_blocks = [b for b in result.content if b["type"] == "image_url"]
        assert len(image_blocks) == 2

    def test_encoding_failure_graceful_degradation(self):
        """测试：图片编码失败时降级处理，仍返回可用 HumanMessage"""
        mock_models = {
            "qwen": {"is_multimodal": True}
        }

        with patch("src.utils.multimodal_message.AVAILABLE_MODELS", mock_models):
            with patch("src.utils.multimodal_message.encode_image_to_base64", side_effect=Exception("文件不存在")):
                result = build_multimodal_message(
                    "请分析图片",
                    image_paths=["/invalid/path.jpg"],
                    model_id="qwen"
                )

        assert isinstance(result, HumanMessage)
        assert isinstance(result.content, list)
        # 只有文本 block，没有图片 block
        assert len(result.content) == 1
        assert result.content[0]["type"] == "text"
        # 降级提示已添加到文本中
        assert "[图片读取失败: /invalid/path.jpg]" in result.content[0]["text"]

    def test_mime_type_inference_jpeg(self):
        """测试：MIME 类型推断 - .jpg 文件"""
        mock_models = {"qwen": {"is_multimodal": True}}
        mock_base64 = "testbase64"

        with patch("src.utils.multimodal_message.AVAILABLE_MODELS", mock_models):
            with patch("src.utils.multimodal_message.encode_image_to_base64", return_value=mock_base64):
                result = build_multimodal_message(
                    "text",
                    image_paths=["/path/image.jpg"],
                    model_id="qwen"
                )

        image_block = result.content[1]
        assert "image/jpeg" in image_block["image_url"]["url"]

    def test_mime_type_inference_png(self):
        """测试：MIME 类型推断 - .png 文件"""
        mock_models = {"qwen": {"is_multimodal": True}}
        mock_base64 = "testbase64"

        with patch("src.utils.multimodal_message.AVAILABLE_MODELS", mock_models):
            with patch("src.utils.multimodal_message.encode_image_to_base64", return_value=mock_base64):
                result = build_multimodal_message(
                    "text",
                    image_paths=["/path/image.png"],
                    model_id="qwen"
                )

        image_block = result.content[1]
        assert "image/png" in image_block["image_url"]["url"]

    def test_mime_type_unknown_defaults_to_jpeg(self):
        """测试：未知 MIME 类型默认为 image/jpeg"""
        mock_models = {"qwen": {"is_multimodal": True}}
        mock_base64 = "testbase64"

        with patch("src.utils.multimodal_message.AVAILABLE_MODELS", mock_models):
            with patch("src.utils.multimodal_message.encode_image_to_base64", return_value=mock_base64):
                # 使用无扩展名的文件路径
                result = build_multimodal_message(
                    "text",
                    image_paths=["/path/unknownfile"],
                    model_id="qwen"
                )

        image_block = result.content[1]
        assert "image/jpeg" in image_block["image_url"]["url"]

    def test_unknown_model_defaults_to_non_multimodal(self):
        """测试：未知模型默认为非多模态"""
        result = build_multimodal_message(
            "text",
            image_paths=["/path/img.jpg"],
            model_id="unknown_model"
        )

        assert isinstance(result.content, str)
        assert "[图片路径 1: /path/img.jpg]" in result.content

    def test_no_model_id_defaults_to_non_multimodal(self):
        """测试：未指定 model_id 时默认为非多模态"""
        result = build_multimodal_message(
            "text",
            image_paths=["/path/img.jpg"],
            model_id=None
        )

        assert isinstance(result.content, str)
        assert "[图片路径 1: /path/img.jpg]" in result.content


class TestIsModelMultimodal:
    """测试 is_model_multimodal 辅助函数"""

    def test_multimodal_model_returns_true(self):
        """测试：多模态模型返回 True"""
        mock_models = {"qwen": {"is_multimodal": True}}

        with patch("src.utils.multimodal_message.AVAILABLE_MODELS", mock_models):
            assert is_model_multimodal("qwen") is True

    def test_non_multimodal_model_returns_false(self):
        """测试：非多模态模型返回 False"""
        mock_models = {"deepseek": {"is_multimodal": False}}

        with patch("src.utils.multimodal_message.AVAILABLE_MODELS", mock_models):
            assert is_model_multimodal("deepseek") is False

    def test_unknown_model_returns_false(self):
        """测试：未知模型返回 False"""
        mock_models = {}

        with patch("src.utils.multimodal_message.AVAILABLE_MODELS", mock_models):
            assert is_model_multimodal("unknown") is False

    def test_none_model_id_returns_false(self):
        """测试：model_id 为 None 时返回 False"""
        assert is_model_multimodal(None) is False

    def test_model_without_config_returns_false(self):
        """测试：模型配置中没有 is_multimodal 字段时返回 False"""
        mock_models = {"some_model": {"name": "Some Model"}}

        with patch("src.utils.multimodal_message.AVAILABLE_MODELS", mock_models):
            assert is_model_multimodal("some_model") is False


class TestExtractImageFromMessages:
    """测试 extract_image_from_messages 函数"""

    def test_openai_compatible_image_url_format(self):
        """测试：解析 OpenAI 兼容格式的 image_url data URL"""
        base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB"
        messages = [
            HumanMessage(content=[
                {"type": "text", "text": "请检测这张图片"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}
                }
            ])
        ]

        result = extract_image_from_messages(messages)

        assert result is not None
        assert result["base64"] == base64_data
        assert result["mime_type"] == "image/jpeg"

    def test_openai_compatible_png_format(self):
        """测试：解析 PNG 格式的 image_url"""
        base64_data = "pngBase64Data"
        messages = [
            HumanMessage(content=[
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_data}"}}
            ])
        ]

        result = extract_image_from_messages(messages)

        assert result is not None
        assert result["base64"] == base64_data
        assert result["mime_type"] == "image/png"

    def test_langchain_standard_image_block_format(self):
        """测试：解析 LangChain 标准格式的 image block"""
        base64_data = "langchainBase64"
        messages = [
            HumanMessage(content=[
                {"type": "text", "text": "分析图片"},
                {
                    "type": "image",
                    "base64": base64_data,
                    "mime_type": "image/jpeg"
                }
            ])
        ]

        result = extract_image_from_messages(messages)

        assert result is not None
        assert result["base64"] == base64_data
        assert result["mime_type"] == "image/jpeg"

    def test_langchain_image_block_without_mime_type_defaults(self):
        """测试：LangChain image block 无 mime_type 时默认为 image/jpeg"""
        base64_data = "langchainBase64"
        messages = [
            HumanMessage(content=[
                {"type": "image", "base64": base64_data}
            ])
        ]

        result = extract_image_from_messages(messages)

        assert result is not None
        assert result["mime_type"] == "image/jpeg"

    def test_text_path_format_extraction(self):
        """测试：从文本消息中提取图片路径"""
        messages = [
            HumanMessage(content="请检测这张图片\n\n[图片路径 1: /uploads/test.jpg]")
        ]

        result = extract_image_from_messages(messages)

        assert result is not None
        assert result["path"] == "/uploads/test.jpg"

    def test_text_path_format_with_spaces(self):
        """测试：路径格式带空格时的提取"""
        messages = [
            HumanMessage(content="[图片路径 2:  /path/to/image.png  ]")
        ]

        result = extract_image_from_messages(messages)

        assert result is not None
        # strip() 会去除两端空格
        assert result["path"] == "/path/to/image.png"

    def test_reverse_traversal_gets_latest_image(self):
        """测试：反向遍历取到最近一条含图片的 HumanMessage"""
        base64_old = "oldImageData"
        base64_new = "newImageData"

        messages = [
            HumanMessage(content=[
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_old}"}}
            ]),
            AIMessage(content="好的，我来分析"),
            HumanMessage(content=[
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_new}"}}
            ]),
        ]

        result = extract_image_from_messages(messages)

        # 应返回最后一条（索引 2）的图片数据
        assert result is not None
        assert result["base64"] == base64_new
        assert result["mime_type"] == "image/png"

    def test_reverse_traversal_with_path_format(self):
        """测试：反向遍历时正确提取路径格式的最新图片"""
        messages = [
            HumanMessage(content="[图片路径 1: /old/path.jpg]"),
            AIMessage(content="分析完成"),
            HumanMessage(content="[图片路径 2: /new/path.jpg]"),
        ]

        result = extract_image_from_messages(messages)

        assert result is not None
        assert result["path"] == "/new/path.jpg"

    def test_no_image_returns_none(self):
        """测试：未找到图片时返回 None"""
        messages = [
            HumanMessage(content="请帮我分析农作物病虫害"),
            AIMessage(content="好的，请描述一下症状"),
        ]

        result = extract_image_from_messages(messages)

        assert result is None

    def test_empty_messages_returns_none(self):
        """测试：空消息列表返回 None"""
        result = extract_image_from_messages([])

        assert result is None

    def test_only_ai_messages_returns_none(self):
        """测试：只有 AIMessage 时返回 None"""
        messages = [
            AIMessage(content="你好"),
            AIMessage(content="有什么可以帮助你的？"),
        ]

        result = extract_image_from_messages(messages)

        assert result is None

    def test_skips_non_data_url_image_url(self):
        """测试：image_url 格式但非 data URL 时返回 None"""
        messages = [
            HumanMessage(content=[
                {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
            ])
        ]

        result = extract_image_from_messages(messages)

        # 非 data URL 格式，应返回 None
        assert result is None

    def test_empty_base64_in_image_block_returns_none(self):
        """测试：image block 中 base64 为空时跳过"""
        messages = [
            HumanMessage(content=[
                {"type": "image", "base64": ""}
            ])
        ]

        result = extract_image_from_messages(messages)

        assert result is None


def main():
    """运行所有测试"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    main()
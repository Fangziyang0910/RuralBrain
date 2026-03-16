"""
模型管理模块

提供统一的接口来管理和创建不同供应商的大语言模型实例

支持的供应商:
- deepseek: DeepSeek 文本模型
- glm: 智谱AI (GLM) 文本模型
- qwen: 通义千问文本模型（OpenAI 兼容格式）
- qwen-vl: 通义千问视觉语言模型（Qwen-VL-Plus，OpenAI 兼容格式）
"""
import os
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI

from ..config import ModelProvider, get_model_config, DEFAULT_TEMPERATURE


class ModelManager:
    """
    大语言模型管理类

    负责根据供应商配置创建和管理不同的模型实例,提供统一的访问接口

    Example:
        >>> manager = ModelManager(provider="deepseek")
        >>> model = manager.get_chat_model()
        >>> # 或者使用自定义配置
        >>> model = manager.get_chat_model(temperature=0.7, model="deepseek-chat")
        >>> # 获取多模态视觉模型
        >>> vision_model = manager.get_vision_model()
    """

    def __init__(
        self,
        provider: ModelProvider = "deepseek",
        api_key: Optional[str] = None,
    ):
        """
        初始化模型管理器

        Args:
            provider: 模型供应商 ("deepseek", "glm", "qwen", "qwen-vl")
            api_key: API密钥,如果为None则从环境变量读取
        """
        self.provider = provider
        self.config = get_model_config(provider)

        # 获取API密钥
        self.api_key = api_key or os.getenv(self.config["api_key_env"])
        if not self.api_key:
            raise ValueError(
                f"未找到 {provider} 的API密钥。"
                f"请设置环境变量 {self.config['api_key_env']} "
                f"或在初始化时传入 api_key 参数"
            )

    def get_chat_model(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> BaseChatModel:
        """
        获取聊天模型实例

        Args:
            model: 模型名称,如果为None则使用默认模型
            temperature: 温度参数,控制输出随机性
            **kwargs: 其他模型特定参数

        Returns:
            BaseChatModel: 符合LangChain规范的聊天模型实例
        """
        model_name = model or self.config["default_model"]
        temp = temperature if temperature is not None else DEFAULT_TEMPERATURE

        if self.provider == "deepseek":
            return self._create_deepseek_model(model_name, temp, **kwargs)
        elif self.provider in ("glm", "qwen", "qwen-vl"):
            return self._create_openai_compatible_model(model_name, temp, **kwargs)
        else:
            raise ValueError(f"不支持的供应商: {self.provider}")

    def get_vision_model(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> ChatOpenAI:
        """
        获取多模态视觉模型实例（Qwen-VL-Plus）

        用于处理图片+文本的多模态输入，支持：
        - 图片描述
        - 图像理解
        - 多图分析

        Args:
            model: 视觉模型名称,默认 qwen-vl-plus
            temperature: 温度参数
            **kwargs: 其他模型参数

        Returns:
            ChatOpenAI: 支持 vision 的聊天模型实例

        Example:
            >>> from langchain_core.messages import HumanMessage
            >>> manager = ModelManager(provider="qwen-vl")
            >>> vision_model = manager.get_vision_model()
            >>> message = HumanMessage(content=[
            ...     {"type": "text", "text": "描述这张图片"},
            ...     {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
            ... ])
            >>> response = vision_model.invoke([message])
        """
        # 如果当前 provider 不是 qwen-vl，创建一个 qwen-vl 的管理器
        if self.provider != "qwen-vl":
            return ModelManager(provider="qwen-vl", api_key=self.api_key).get_vision_model(model, temperature, **kwargs)

        return self.get_chat_model(model, temperature, **kwargs)

    def _create_deepseek_model(
        self,
        model: str,
        temperature: float,
        **kwargs
    ) -> ChatDeepSeek:
        """创建 DeepSeek 模型实例"""
        return ChatDeepSeek(
            model=model,
            api_key=self.api_key,
            temperature=temperature,
            **kwargs
        )

    def _create_openai_compatible_model(
        self,
        model: str,
        temperature: float,
        **kwargs
    ) -> ChatOpenAI:
        """创建 OpenAI 兼容模型实例（GLM、Qwen、Qwen-VL）"""
        base_url = self.config.get("base_url")

        return ChatOpenAI(
            model=model,
            api_key=self.api_key,
            base_url=base_url,
            temperature=temperature,
            **kwargs
        )

    @classmethod
    def from_env(cls, provider_env: str = "MODEL_PROVIDER") -> "ModelManager":
        """
        从环境变量创建模型管理器

        Args:
            provider_env: 存储供应商名称的环境变量名

        Returns:
            ModelManager: 模型管理器实例
        """
        provider = os.getenv(provider_env, "deepseek")  # type: ignore
        return cls(provider=provider)

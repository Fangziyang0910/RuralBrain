"""
模型管理模块

提供统一的接口来管理和创建不同供应商的大语言模型实例
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
    
    支持的供应商:
    - deepseek: DeepSeek 模型
    - glm: 智谱AI (GLM) 模型
    
    Example:
        >>> manager = ModelManager(provider="deepseek")
        >>> model = manager.get_chat_model()
        >>> # 或者使用自定义配置
        >>> model = manager.get_chat_model(temperature=0.7, model="deepseek-chat")
    """
    
    def __init__(
        self,
        provider: ModelProvider = "deepseek",
        api_key: Optional[str] = None,
    ):
        """
        初始化模型管理器
        
        Args:
            provider: 模型供应商 ("deepseek" 或 "glm")
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
        elif self.provider == "glm":
            return self._create_glm_model(model_name, temp, **kwargs)
        else:
            raise ValueError(f"不支持的供应商: {self.provider}")
    
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
    
    def _create_glm_model(
        self,
        model: str,
        temperature: float,
        **kwargs
    ) -> ChatOpenAI:
        """创建智谱AI (GLM) 模型实例 - 使用 OpenAI 兼容接口"""
        return ChatOpenAI(
            model=model,
            api_key=self.api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4/",
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

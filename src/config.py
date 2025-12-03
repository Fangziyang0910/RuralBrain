"""
RuralBrain 配置管理模块

统一管理系统配置,包括模型供应商、API密钥等设置
"""
import os
from typing import Literal

# 模型供应商类型
ModelProvider = Literal["deepseek", "glm"]

# 默认配置
DEFAULT_PROVIDER: ModelProvider = os.getenv("MODEL_PROVIDER", "deepseek")  # type: ignore
DEFAULT_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0"))

# 模型配置映射
MODEL_CONFIGS = {
    "deepseek": {
        "default_model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "glm": {
        "default_model": "glm-4",  # 或 glm-4-plus, glm-4-air, glm-4-flash
        "api_key_env": "ZHIPUAI_API_KEY",
    },
}


def get_model_config(provider: ModelProvider) -> dict:
    """
    获取指定供应商的模型配置
    
    Args:
        provider: 模型供应商名称
        
    Returns:
        包含模型配置信息的字典
        
    Raises:
        ValueError: 如果供应商不支持
    """
    if provider not in MODEL_CONFIGS:
        raise ValueError(
            f"不支持的模型供应商: {provider}. "
            f"支持的供应商: {list(MODEL_CONFIGS.keys())}"
        )
    return MODEL_CONFIGS[provider]

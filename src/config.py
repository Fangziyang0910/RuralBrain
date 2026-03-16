"""RuralBrain 配置管理"""
import os
from typing import Literal

# 模型配置
ModelProvider = Literal["deepseek", "glm", "qwen", "qwen-vl"]

DEFAULT_PROVIDER: ModelProvider = os.getenv("MODEL_PROVIDER", "deepseek")
DEFAULT_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "2000"))

MODEL_CONFIGS = {
    "deepseek": {"default_model": "deepseek-chat", "api_key_env": "DEEPSEEK_API_KEY"},
    "glm": {"default_model": "glm-4", "api_key_env": "ZHIPUAI_API_KEY"},
    "qwen": {
        "default_model": "qwen-plus",
        "api_key_env": "QWEN_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    },
    # 多模态视觉语言模型（Qwen-VL-Plus）
    # 使用阿里云百炼 OpenAI 兼容格式
    "qwen-vl": {
        "default_model": "qwen-vl-plus",
        "api_key_env": "QWEN_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    },
}


# LangSmith 配置
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

# 检测服务配置
DETECTION_ENDPOINTS = {
    "pest": os.getenv("PEST_DETECTION_API_URL", "http://localhost:8001/detection/pest/detect"),
    "rice": os.getenv("RICE_DETECTION_API_URL", "http://localhost:8001/detection/rice/predict"),
    "cow": os.getenv("COW_DETECTION_API_URL", "http://localhost:8001/detection/cow/detect"),
}

# 知识库配置
KNOWLEDGE_BASE_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base")

# RAG 配置
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
RETRIEVE_SCORE_THRESHOLD = float(os.getenv("RETRIEVE_SCORE_THRESHOLD", "0.7"))

# Embedding 配置
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-zh-v1.5")
EMBEDDING_DEVICE: Literal["cpu", "cuda", "mps"] = os.getenv("EMBEDDING_DEVICE", "cpu")

# 技能中间件配置
SkillReloadStrategy = Literal["always", "timed", "never"]
SKILL_RELOAD_STRATEGY: SkillReloadStrategy = os.getenv("SKILL_RELOAD_STRATEGY", "never")
SKILL_RELOAD_INTERVAL = int(os.getenv("SKILL_RELOAD_INTERVAL", "300"))  # 秒

# 工具 TTL 配置
DEFAULT_TOOL_TTL = int(os.getenv("DEFAULT_TOOL_TTL", "3"))  # 默认工具生命周期（轮数）
DEFAULT_TOOL_EXTENSION = int(os.getenv("DEFAULT_TOOL_EXTENSION", "2"))  # 默认续期增量（轮数）
ENABLE_TOOL_TTL = os.getenv("ENABLE_TOOL_TTL", "true").lower() == "true"  # 是否启用 TTL 机制


def get_model_config(provider: ModelProvider) -> dict:
    """获取指定供应商的模型配置"""
    if provider not in MODEL_CONFIGS:
        raise ValueError(f"不支持的模型供应商: {provider}. 支持的供应商: {list(MODEL_CONFIGS.keys())}")
    return MODEL_CONFIGS[provider]

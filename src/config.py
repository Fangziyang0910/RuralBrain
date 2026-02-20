"""RuralBrain 配置管理"""
import os
from typing import Literal

# 模型配置
ModelProvider = Literal["deepseek", "glm"]

DEFAULT_PROVIDER: ModelProvider = os.getenv("MODEL_PROVIDER", "deepseek")
DEFAULT_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "2000"))

MODEL_CONFIGS = {
    "deepseek": {"default_model": "deepseek-chat", "api_key_env": "DEEPSEEK_API_KEY"},
    "glm": {"default_model": "glm-4", "api_key_env": "ZHIPUAI_API_KEY"},
}


# LangSmith 配置
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

# 服务配置
PLANNING_SERVICE_URL = os.getenv("PLANNING_SERVICE_URL", "http://localhost:8003")

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


def get_model_config(provider: ModelProvider) -> dict:
    """获取指定供应商的模型配置"""
    if provider not in MODEL_CONFIGS:
        raise ValueError(f"不支持的模型供应商: {provider}. 支持的供应商: {list(MODEL_CONFIGS.keys())}")
    return MODEL_CONFIGS[provider]

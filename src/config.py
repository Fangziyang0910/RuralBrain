"""
RuralBrain 配置管理模块

统一管理系统配置,包括模型供应商、API密钥等设置
"""
import os
from typing import Literal

# ============================================
# 模型配置
# ============================================
# 模型供应商类型
ModelProvider = Literal["deepseek", "glm"]

# 默认配置
DEFAULT_PROVIDER: ModelProvider = os.getenv("MODEL_PROVIDER", "deepseek")  # type: ignore
DEFAULT_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
MODEL_MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "2000"))

# ============================================
# Agent 配置
# ============================================
# Agent 版本: v1（传统架构）或 v2（Skills 架构，推荐）
AGENT_VERSION: Literal["v1", "v2"] = os.getenv("AGENT_VERSION", "v2")  # type: ignore

# V2 Agent 失败时是否自动回退到 V1
AGENT_AUTO_FALLBACK = os.getenv("AGENT_AUTO_FALLBACK", "true").lower() == "true"

# ============================================
# LangSmith 配置（可选，用于调试）
# ============================================
# 是否启用 LangSmith 追踪
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

# 是否在后台运行回调
LANGCHAIN_CALLBACKS_BACKGROUND = os.getenv("LANGCHAIN_CALLBACKS_BACKGROUND", "false").lower() == "true"

# ============================================
# 服务配置
# ============================================
# 规划咨询服务地址
PLANNING_SERVICE_URL = os.getenv("PLANNING_SERVICE_URL", "http://localhost:8003")

# 检测服务地址（统一网关）
PEST_DETECTION_API_URL = os.getenv("PEST_DETECTION_API_URL", "http://localhost:8001/detection/pest/detect")
RICE_DETECTION_API_URL = os.getenv("RICE_DETECTION_API_URL", "http://localhost:8001/detection/rice/predict")
COW_DETECTION_API_URL = os.getenv("COW_DETECTION_API_URL", "http://localhost:8001/detection/cow/detect")

# ============================================
# 知识库配置
# ============================================
# 知识库路径
KNOWLEDGE_BASE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", "knowledge_base")
KNOWLEDGE_BASE_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base")

# ============================================
# RAG 配置
# ============================================
# 文本分块配置
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# 检索配置
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
RETRIEVE_SCORE_THRESHOLD = float(os.getenv("RETRIEVE_SCORE_THRESHOLD", "0.7"))

# ============================================
# 向量数据库配置
# ============================================
# 向量数据库类型: chroma, faiss, qdrant
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chroma")

# Embedding 模型配置
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-zh-v1.5")
EMBEDDING_DEVICE: Literal["cpu", "cuda", "mps"] = os.getenv("EMBEDDING_DEVICE", "cpu")  # type: ignore

# ============================================
# 缓存配置
# ============================================
# 向量缓存最大大小（MB）
MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", "400"))

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

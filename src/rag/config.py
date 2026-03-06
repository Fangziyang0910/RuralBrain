"""
RAG 知识库配置
支持环境变量覆盖，适配 Docker 部署
"""
import os
from pathlib import Path
from typing import Literal

# ==================== 项目路径配置 ====================
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = SRC_DIR / "data"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"

# ==================== 向量数据库配置 ====================
# 支持的环境变量
VECTOR_DB_TYPE: Literal["chroma", "faiss", "qdrant"] = os.getenv(
    "VECTOR_DB_TYPE", "chroma"
)

# Chroma 配置（默认）
CHROMA_PERSIST_DIR = KNOWLEDGE_BASE_DIR / "chroma_db"
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "rural_planning")

# FAISS 配置（可选）
FAISS_INDEX_PATH = KNOWLEDGE_BASE_DIR / "faiss_index"

# Qdrant 配置（生产环境推荐）
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rural_planning")

# ==================== Embedding 模型配置 ====================
# Embedding Provider: dashscope（千问，默认）, local（本地模型）, openai
# 优先使用千问 API，密钥缺失时自动降级到本地模型
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "dashscope")

# 千问 API 配置（默认，使用 OpenAI 兼容格式）
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_EMBEDDING_MODEL = os.getenv(
    "QWEN_EMBEDDING_MODEL",
    "text-embedding-v4"  # 千问 Embedding 模型
)

# 本地模型配置（降级方案）
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "BAAI/bge-small-zh-v1.5"  # 中文 Embedding 模型
)
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")  # 可选: cuda, mps

# OpenAI 配置（可选）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_EMBEDDING_MODEL = os.getenv(
    "OPENAI_EMBEDDING_MODEL",
    "text-embedding-3-small"
)

# ==================== 文本分割配置 ====================
# 针对 Planning Agent 优化：更大的 chunk_size 保留更多上下文
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "2500"))  # 默认 2500（比传统 RAG 更大）
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "500"))  # 默认 500
ADD_START_INDEX = os.getenv("ADD_START_INDEX", "true").lower() == "true"

# ==================== 检索配置 ====================
# Planning Agent 需要更多上下文，默认返回更多文档
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
RETRIEVE_SCORE_THRESHOLD = float(os.getenv("RETRIEVE_SCORE_THRESHOLD", "0.7"))

# 检索策略配置
# 支持的策略: "similarity"（相似度）, "mmr"（最大边际相关性）, "similarity_score_threshold"（带阈值过滤）
RETRIEVE_SEARCH_TYPE = os.getenv("RETRIEVE_SEARCH_TYPE", "similarity_score_threshold")

# MMR 检索参数（用于最大边际相关性检索，增加结果多样性）
MMR_LAMBDA_MULT = float(os.getenv("MMR_LAMBDA_MULT", "0.7"))  # 多样性权重，0-1，越高越多样化

# ==================== 日志配置 ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ==================== LLM 模型配置 ====================
# 从主配置导入模型供应商配置
DEFAULT_PROVIDER = os.getenv("MODEL_PROVIDER", "deepseek")

# ==================== Docker 部署检测 ====================
def is_docker() -> bool:
    """检测是否运行在 Docker 容器中"""
    return Path("/.dockerenv").exists() or os.path.exists("/.dockerenv")

# ==================== 验证配置 ====================
def validate_config() -> None:
    """验证配置是否有效"""
    # 确保目录存在
    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 验证向量数据库类型
    valid_db_types = ["chroma", "faiss", "qdrant"]
    if VECTOR_DB_TYPE not in valid_db_types:
        raise ValueError(
            f"无效的 VECTOR_DB_TYPE: {VECTOR_DB_TYPE}. "
            f"可选值: {valid_db_types}"
        )

    # 验证 chunk_size
    if CHUNK_SIZE < 100:
        raise ValueError(f"CHUNK_SIZE 太小: {CHUNK_SIZE}，最小值为 100")

    if CHUNK_OVERLAP >= CHUNK_SIZE:
        raise ValueError(
            f"CHUNK_OVERLAP ({CHUNK_OVERLAP}) "
            f"不能大于等于 CHUNK_SIZE ({CHUNK_SIZE})"
        )


# 初始化时验证
validate_config()


# ==================== Embedding 单例缓存 ====================
_embedding_instance = None
_embedding_lock = None


def _get_embedding_lock():
    """获取 Embedding 初始化锁"""
    global _embedding_lock
    if _embedding_lock is None:
        import threading
        _embedding_lock = threading.Lock()
    return _embedding_lock


def get_embeddings_cached():
    """
    获取 Embedding 实例（单例缓存模式）

    优先使用缓存的实例，避免重复加载模型。
    如需强制重新加载，调用 reset_embeddings_cache()

    Returns:
        LangChain Embeddings 单例实例
    """
    global _embedding_instance
    if _embedding_instance is not None:
        return _embedding_instance

    with _get_embedding_lock():
        # 双重检查
        if _embedding_instance is None:
            _embedding_instance = get_embeddings()
        return _embedding_instance


def reset_embeddings_cache():
    """重置 Embedding 缓存（主要用于测试）"""
    global _embedding_instance
    _embedding_instance = None


# ==================== Embedding 工厂函数 ====================
def get_embeddings():
    """
    获取 Embedding 实例（支持多种 Provider）

    优先级：
    1. 千问 API (dashscope) - 默认方案（密钥缺失时自动降级到本地模型）
    2. OpenAI API - 备选方案
    3. 本地模型 - 降级方案

    Returns:
        LangChain Embeddings 实例
    """
    provider = EMBEDDING_PROVIDER.lower()

    # 千问 API（默认，使用 OpenAI 兼容格式）
    if provider == "dashscope":
        if QWEN_API_KEY:
            try:
                from langchain_openai import OpenAIEmbeddings
                import logging
                logging.info(f"使用千问 Embedding: {QWEN_EMBEDDING_MODEL}")
                return OpenAIEmbeddings(
                    model=QWEN_EMBEDDING_MODEL,
                    openai_api_key=QWEN_API_KEY,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
            except ImportError:
                pass
        # 千问不可用，降级到本地模型
        import logging
        logging.warning("千问 API 密钥未配置或依赖缺失，降级到本地 Embedding 模型")
        return _get_local_embeddings()

    # OpenAI API
    elif provider == "openai":
        if OPENAI_API_KEY:
            try:
                from langchain_openai import OpenAIEmbeddings
                import logging
                logging.info(f"使用 OpenAI Embedding: {OPENAI_EMBEDDING_MODEL}")
                return OpenAIEmbeddings(
                    model=OPENAI_EMBEDDING_MODEL,
                    openai_api_key=OPENAI_API_KEY
                )
            except ImportError:
                pass
        # OpenAI 不可用，降级到本地模型
        import logging
        logging.warning("OpenAI API 密钥未配置或依赖缺失，降级到本地 Embedding 模型")
        return _get_local_embeddings()

    # 本地（默认降级方案）
    else:
        return _get_local_embeddings()


def _get_local_embeddings():
    """获取本地 Embedding 模型（降级方案）"""
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        import logging
        logging.info(f"使用本地 Embedding 模型: {EMBEDDING_MODEL_NAME}")
        return HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={'device': EMBEDDING_DEVICE},
            encode_kwargs={
                'normalize_embeddings': True,  # 归一化向量
            }
        )
    except ImportError:
        raise ImportError(
            "本地 Embedding 需要 langchain-community 和 sentence-transformers 依赖\n"
            "请运行: uv add langchain-community sentence-transformers"
        )

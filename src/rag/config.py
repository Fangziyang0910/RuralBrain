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
# Embedding Provider: local（本地模型）, dashscope（千问）, openai
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")

# 本地模型配置（降级方案）
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "BAAI/bge-small-zh-v1.5"  # 中文 Embedding 模型
)
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")  # 可选: cuda, mps

# 千问 API 配置（推荐）
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_EMBEDDING_MODEL = os.getenv(
    "DASHSCOPE_EMBEDDING_MODEL",
    "text-embedding-v3"  # 千问 Embedding 模型
)

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


# ==================== Embedding 工厂函数 ====================
def get_embeddings():
    """
    获取 Embedding 实例（支持多种 Provider）

    优先级：
    1. 千问 API (dashscope) - 推荐，无需本地模型
    2. OpenAI API - 备选方案
    3. 本地模型 - 降级方案

    Returns:
        LangChain Embeddings 实例
    """
    provider = EMBEDDING_PROVIDER.lower()

    # 千问 API（推荐）
    if provider == "dashscope":
        if not DASHSCOPE_API_KEY:
            raise ValueError(
                "使用千问 Embedding 需要配置 DASHSCOPE_API_KEY\n"
                "请获取 API Key: https://help.aliyun.com/zh/dashscope/developer-reference/activate-dashscope\n"
                "然后设置环境变量: export DASHSCOPE_API_KEY=your_key"
            )
        try:
            from langchain_community.embeddings import DashScopeEmbeddings
            return DashScopeEmbeddings(
                model=DASHSCOPE_EMBEDDING_MODEL,
                dashscope_api_key=DASHSCOPE_API_KEY
            )
        except ImportError:
            raise ImportError(
                "千问 Embedding 需要 langchain-community 依赖\n"
                "请运行: uv add langchain-community"
            )

    # OpenAI API
    elif provider == "openai":
        if not OPENAI_API_KEY:
            raise ValueError(
                "使用 OpenAI Embedding 需要配置 OPENAI_API_KEY"
            )
        try:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                model=OPENAI_EMBEDDING_MODEL,
                openai_api_key=OPENAI_API_KEY
            )
        except ImportError:
            raise ImportError(
                "OpenAI Embedding 需要 langchain-openai 依赖\n"
                "请运行: uv add langchain-openai"
            )

    # 本地模型（降级方案）
    elif provider == "local":
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

    else:
        raise ValueError(
            f"不支持的 EMBEDDING_PROVIDER: {provider}\n"
            f"可选值: local, dashscope, openai"
        )

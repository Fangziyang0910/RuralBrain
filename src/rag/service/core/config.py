"""
Planning Service 服务配置
独立于 RAG 模块配置，专门用于 FastAPI 服务
"""
import os
from pathlib import Path
from typing import List

# ==================== 服务基础配置 ====================
SERVICE_NAME = "planning-service"
SERVICE_VERSION = "1.0.0"

# 端口配置
SERVICE_PORT = int(os.getenv("PLANNING_SERVICE_PORT", "8003"))
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")

# ==================== CORS 配置 ====================
ALLOWED_ORIGINS: List[str] = os.getenv(
    "ALLOWED_ORIGINS", "*"
).split(",") if os.getenv("ALLOWED_ORIGINS") != "*" else ["*"]

ALLOWED_METHODS = ["GET", "POST", "OPTIONS"]
ALLOWED_HEADERS = ["*"]

# ==================== API 配置 ====================
API_PREFIX = "/api/v1"

# SSE 流式响应配置
STREAM_RESPONSE_TIMEOUT = int(os.getenv("STREAM_RESPONSE_TIMEOUT", "120"))  # 秒

# ==================== 日志配置 ====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ==================== 健康检查配置 ====================
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))  # 秒

# ==================== 知识库配置 ====================
# 继承自 RAG 模块配置
KNOWLEDGE_BASE_PATH = os.getenv("KNOWLEDGE_BASE_PATH", "/app/knowledge_base")
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "chroma")

# ==================== LLM 配置 ====================
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "deepseek")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0"))

# ==================== 响应缓存配置（可选）====================
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "false").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 秒

# ==================== 环境信息 ====================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# ==================== 验证配置 ====================
def validate_config() -> None:
    """验证服务配置"""
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if LOG_LEVEL not in valid_log_levels:
        raise ValueError(
            f"无效的 LOG_LEVEL: {LOG_LEVEL}. 可选值: {valid_log_levels}"
        )

    if not (1 <= SERVICE_PORT <= 65535):
        raise ValueError(f"无效的 SERVICE_PORT: {SERVICE_PORT}")

    if MODEL_PROVIDER not in ["deepseek", "glm", "openai"]:
        raise ValueError(
            f"无效的 MODEL_PROVIDER: {MODEL_PROVIDER}"
        )


# 初始化时验证
validate_config()

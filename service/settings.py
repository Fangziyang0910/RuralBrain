"""
服务配置
"""
import os
import tempfile
from pathlib import Path
from typing import List

# 项目根目录路径
BASE_DIR = Path(__file__).parent.parent

# 上传文件存储目录（使用系统临时目录，跨平台兼容）
UPLOAD_DIR = Path(tempfile.gettempdir()) / "ruralbrain_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# CORS 配置
# CORS 跨域白名单
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# 服务配置
# 服务监听地址和端口
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8080"))

# 文件上传配置
# 文件大小限制
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
# 支持的图片格式
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# ============================================
# Agent 配置
# ============================================
# Agent 版本选择
AGENT_VERSION = os.getenv("AGENT_VERSION", "v1").lower()
# V2 Agent 失败时是否自动回退到 V1
AGENT_AUTO_FALLBACK = os.getenv("AGENT_AUTO_FALLBACK", "true").lower() == "true"

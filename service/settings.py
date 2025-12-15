"""
服务配置
"""
import os
from pathlib import Path
from typing import List

# 项目根目录路径
BASE_DIR = Path(__file__).parent.parent

# 上传文件存储目录
UPLOAD_DIR = BASE_DIR / "uploads"
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

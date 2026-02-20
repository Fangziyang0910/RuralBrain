"""
服务配置
"""
import os
import tempfile
from pathlib import Path
from typing import List

# 项目根目录路径
BASE_DIR = Path(__file__).parent.parent

# ============================================
# 临时文件存储配置（简洁版：LRU 缓存）
# ============================================

# 临时文件根目录（统一放在系统临时目录）
TEMP_DIR = Path(tempfile.gettempdir()) / "ruralbrain"
TEMP_DIR.mkdir(exist_ok=True)

# 上传文件目录
UPLOAD_DIR = TEMP_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 检测结果目录
DETECTION_RESULTS_DIR = TEMP_DIR / "detection_results"
DETECTION_RESULTS_DIR.mkdir(exist_ok=True)

# 创建所有检测类型的子目录（确保静态文件挂载能正常工作）
for detection_type in ["pest", "cow", "rice"]:
    (DETECTION_RESULTS_DIR / detection_type).mkdir(exist_ok=True)

# 缓存容量限制（默认 500MB）
MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", "500")) * 1024 * 1024

# CORS 配置
# CORS 跨域白名单
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3001").split(",")

# 服务配置
# 服务监听地址和端口
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8081"))

# 文件上传配置
# 文件大小限制
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
# 支持的图片格式
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


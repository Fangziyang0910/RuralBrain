from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类"""
    # 项目基本配置
    PROJECT_NAME: str = "Cow Detection API"
    VERSION: str = "1.0.0"
    
    # 获取detector目录的绝对路径
    DETECTOR_DIR: Path = Path(__file__).parent.parent.parent
    
    # 模型配置 - 在容器内和本地使用不同路径
    if os.path.exists("/app"):
        # 容器内环境
        MODEL_PATH: str = "/app/models/yolov8n.pt"
    else:
        # 本地环境 - 修正路径指向detector/models目录
        MODEL_PATH: str = str(DETECTOR_DIR / "models" / "yolov8n.pt")
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # 检测配置
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.5
    DEFAULT_VIDEO_SAMPLE_RATE: int = 10
    
    # 文件上传配置
    UPLOAD_DIR: str = str(DETECTOR_DIR / "uploads")
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # 类别文件配置
    CLASSES_PATH: str = str(DETECTOR_DIR / "models" / "classes.txt")
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # 忽略额外的环境变量


# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.DETECTOR_DIR / "models", exist_ok=True)
# 在容器内和本地都使用detector目录下的uploads
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
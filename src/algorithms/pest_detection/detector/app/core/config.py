from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类"""
    # 项目基本配置
    PROJECT_NAME: str = "Insect Detector API"
    VERSION: str = "1.0.0"
    
    # 获取detector目录的绝对路径
    DETECTOR_DIR: Path = Path(__file__).parent.parent.parent
    
    # 模型配置 - 使用绝对路径
    MODEL_PATH: str = str(DETECTOR_DIR / "models" / "best.pt")
    CLASSES_PATH: str = str(DETECTOR_DIR / "models" / "classes.txt")
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000  # 病虫害检测服务
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # 忽略额外的环境变量


# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.DETECTOR_DIR / "models", exist_ok=True)
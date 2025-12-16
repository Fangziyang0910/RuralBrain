from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """大米检测应用配置类"""
    # 项目基本配置
    PROJECT_NAME: str = "大米品种识别API"
    VERSION: str = "1.0.0"
    
    # 获取detector目录的绝对路径
    DETECTOR_DIR: Path = Path(__file__).parent.parent.parent
    
    # 模型配置 - 使用detector/models目录下的模型
    WEIGHTS_PATH_FL: str = str(DETECTOR_DIR / "models" / "weights_fl" / "best.pt")
    WEIGHTS_PATH_XJ: str = str(DETECTOR_DIR / "models" / "weights_xj" / "best.pt")
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8081
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # 忽略额外的环境变量


# 创建全局配置实例
settings = Settings()

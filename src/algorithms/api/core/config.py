"""
统一算法服务配置
"""
from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    """统一算法服务配置类"""

    # 项目基本配置
    PROJECT_NAME: str = "RuralBrain 算法服务"
    VERSION: str = "2.0.0"

    # 获取 algorithms 目录的绝对路径
    # __file__ = /app/api/main.py
    # parent.parent = /app/algorithms
    ALGORITHMS_DIR: Path = Path(__file__).parent.parent.parent

    @property
    def DETECTION_DIR(self) -> Path:
        """检测算法目录"""
        return self.ALGORITHMS_DIR / "detection"

    @property
    def MODELS_DIR(self) -> Path:
        """模型文件根目录"""
        return self.DETECTION_DIR / "models"

    # 检测算法模型路径
    @property
    def PEST_MODEL_PATH(self) -> str:
        return str(self.MODELS_DIR / "pest" / "best.pt")

    @property
    def PEST_CLASSES_PATH(self) -> str:
        return str(self.MODELS_DIR / "pest" / "classes.txt")

    @property
    def RICE_MODEL_PATH(self) -> str:
        return str(self.MODELS_DIR / "rice" / "weights_fl" / "best.pt")

    @property
    def COW_MODEL_PATH(self) -> str:
        return str(self.MODELS_DIR / "cow" / "yolov8n.pt")

    @property
    def COW_CLASSES_PATH(self) -> str:
        return str(self.MODELS_DIR / "cow" / "classes.txt")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # 忽略额外的环境变量


# 创建全局配置实例
settings = Settings()

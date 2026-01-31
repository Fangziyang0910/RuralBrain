"""
统一检测服务配置
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """统一检测服务配置类"""

    # 项目基本配置
    PROJECT_NAME: str = "RuralBrain 统一检测服务"
    VERSION: str = "2.0.0"

    # 获取triple_detector目录的绝对路径
    # __file__ = /app/triple_detector/app/core/config.py
    # parent.parent.parent = /app/triple_detector
    TRIPLE_DETECTOR_DIR: Path = Path(__file__).parent.parent.parent

    def get_model_path(self, service_name: str, model_file: str) -> str:
        """
        自动检测模型路径（支持 Docker 和本地开发环境）

        Args:
            service_name: 服务名称（pest/rice/cow）
            model_file: 模型文件名

        Returns:
            str: 模型文件的完整路径
        """
        # Docker 环境：/app/triple_detector/{service}/models/
        docker_path = self.TRIPLE_DETECTOR_DIR / service_name / "models" / model_file
        if docker_path.exists():
            return str(docker_path)

        # 本地开发环境：指向原始的检测服务目录
        # triple_detector 的父目录是 algorithms/
        algorithms_dir = self.TRIPLE_DETECTOR_DIR.parent.parent
        local_path = algorithms_dir / f"{service_name}_detection" / "detector" / "models" / model_file
        if local_path.exists():
            return str(local_path)

        # 都不存在，返回 Docker 路径（让后续代码报错）
        return str(docker_path)

    @property
    def PEST_MODEL_PATH(self) -> str:
        return self.get_model_path("pest", "best.pt")

    @property
    def PEST_CLASSES_PATH(self) -> str:
        return self.get_model_path("pest", "classes.txt")

    @property
    def RICE_MODEL_PATH(self) -> str:
        return self.get_model_path("rice", "weights_fl/best.pt")

    @property
    def COW_MODEL_PATH(self) -> str:
        return self.get_model_path("cow", "yolov8n.pt")

    @property
    def COW_CLASSES_PATH(self) -> str:
        return self.get_model_path("cow", "classes.txt")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # 忽略额外的环境变量


# 创建全局配置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.TRIPLE_DETECTOR_DIR / "pest" / "models", exist_ok=True)
os.makedirs(settings.TRIPLE_DETECTOR_DIR / "rice" / "models", exist_ok=True)
os.makedirs(settings.TRIPLE_DETECTOR_DIR / "cow" / "models", exist_ok=True)
os.makedirs(settings.TRIPLE_DETECTOR_DIR / "uploads", exist_ok=True)

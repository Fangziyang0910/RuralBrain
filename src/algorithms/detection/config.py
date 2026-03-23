"""
检测算法配置

这是检测算法的配置模块，算法代码从此导入配置。
不依赖 FastAPI，可以独立测试。
"""
from pathlib import Path
import os


class DetectionConfig:
    """检测算法配置类"""

    # 获取 detection 目录的绝对路径
    # __file__ = /app/detection/config.py
    # parent = /app/detection
    DETECTION_DIR: Path = Path(__file__).parent

    @property
    def MODELS_DIR(self) -> Path:
        """模型文件根目录"""
        return self.DETECTION_DIR / "models"

    # 模型路径
    @property
    def PEST_MODEL_PATH(self) -> str:
        return str(self.MODELS_DIR / "pest" / "best.onnx")

    @property
    def PEST_CLASSES_PATH(self) -> str:
        return str(self.MODELS_DIR / "pest" / "classes.txt")

    @property
    def RICE_MODEL_PATH(self) -> str:
        return str(self.MODELS_DIR / "rice" / "weights_fl" / "best.onnx")

    @property
    def COW_MODEL_PATH(self) -> str:
        return str(self.MODELS_DIR / "cow" / "yolov8n.onnx")

    @property
    def COW_CLASSES_PATH(self) -> str:
        return str(self.MODELS_DIR / "cow" / "classes.txt")

    @property
    def DISEASE_MODEL_PATH(self) -> str:
        return str(self.MODELS_DIR / "disease" / "best.onnx")

    @property
    def DISEASE_CLASSES_PATH(self) -> str:
        return str(self.MODELS_DIR / "disease" / "classes.txt")


# 创建全局配置实例
config = DetectionConfig()

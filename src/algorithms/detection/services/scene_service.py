"""
场景分类服务
使用图像分类模型识别农场巡检图片的场景类型
支持：牛舍、猪舍、农田
"""
import os
import threading
from typing import Dict, List, Optional
from pathlib import Path

from algorithms.detection.services.onnx_cls import ONNXClassifier
from algorithms.detection.config import config


# 场景类型定义（仅保留三个场景）
SCENE_TYPES = {
    "cattle": {
        "name": "牛舍",
        "description": "奶牛养殖区域",
        "recommended_tools": [
            {"tool": "cow_detection_tool", "reason": "检测牛只数量"},
            {"tool": "disease_prediction_tool", "reason": "分析牛只健康状况"}
        ]
    },
    "pig": {
        "name": "猪舍",
        "description": "生猪养殖区域",
        "recommended_tools": [
            {"tool": "disease_prediction_tool", "reason": "分析猪只健康状况"}
        ]
    },
    "farmland": {
        "name": "农田",
        "description": "农作物种植区域",
        "recommended_tools": [
            {"tool": "pest_detection_tool", "reason": "检测病虫害"},
            {"tool": "plant_disease_detection_tool", "reason": "识别植物病害"}
        ]
    },
    "unknown": {
        "name": "未知场景",
        "description": "无法识别的场景类型",
        "recommended_tools": []
    }
}


class SceneModelService:
    """
    场景分类模型服务类
    线程安全，支持惰性初始化
    TODO: 等场景分类模型训练完成后启用
    """

    def __init__(self):
        """初始化模型服务，但不立即加载模型"""
        self._classifier: Optional[ONNXClassifier] = None
        self._class_names: List[str] = []
        self._initialized: bool = False
        self._init_lock = threading.Lock()
        self._inference_lock = threading.Lock()
        self._model_loaded = False

    def _load_class_names(self) -> List[str]:
        """从 classes.txt 加载类别名称"""
        classes_path = config.SCENE_CLASSES_PATH

        if not os.path.exists(classes_path):
            # 使用默认类别（三个场景）
            return ["cattle", "pig", "farmland"]

        with open(classes_path, 'r', encoding='utf-8') as f:
            classes = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return classes

    def _initialize(self):
        """线程安全的惰性初始化模型"""
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return

            try:
                model_path = config.SCENE_MODEL_PATH

                # 检查模型文件是否存在
                if not os.path.exists(model_path):
                    print(f"[Scene] 模型文件不存在: {model_path}")
                    print(f"[Scene] 场景分类服务将以模拟模式运行")
                    self._model_loaded = False
                    self._class_names = self._load_class_names()
                    self._initialized = True
                    return

                # 加载类别名称
                self._class_names = self._load_class_names()

                # 创建 ONNX 分类器
                self._classifier = ONNXClassifier(
                    model_path=model_path,
                    class_names=self._class_names
                )

                self._model_loaded = True
                print(f"[Scene] 已加载 {len(self._class_names)} 个场景类别")
                self._initialized = True
            except Exception as e:
                print(f"[Scene] 模型初始化失败: {str(e)}")
                print(f"[Scene] 场景分类服务将以模拟模式运行")
                self._model_loaded = False
                self._class_names = self._load_class_names()
                self._initialized = True

    @property
    def classifier(self) -> Optional[ONNXClassifier]:
        """获取分类器实例"""
        self._initialize()
        return self._classifier

    @property
    def class_names(self) -> List[str]:
        """获取类别名称列表"""
        self._initialize()
        return self._class_names

    @property
    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        self._initialize()
        return self._model_loaded

    def classify_scene(self, image_base64: str, top_k: int = 1) -> Dict:
        """
        分类图像的场景类型

        Args:
            image_base64: base64编码的图像字符串
            top_k: 返回前 k 个预测结果

        Returns:
            分类结果字典
        """
        self._initialize()

        # 如果模型未加载，返回模拟结果
        if not self._model_loaded:
            # 默认返回未知场景
            return {
                "success": True,
                "scene_type": "unknown",
                "scene_name": SCENE_TYPES["unknown"]["name"],
                "confidence": 0.0,
                "recommended_tools": SCENE_TYPES["unknown"]["recommended_tools"],
                "mock": True
            }

        try:
            import cv2
            import numpy as np
            import base64

            # 转换base64图像
            img_data = base64.b64decode(image_base64)
            np_arr = np.frombuffer(img_data, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if image is None:
                raise ValueError("无法解码图像数据")

            # 使用线程锁保护推理过程
            with self._inference_lock:
                # 进行预测
                predictions, _ = self.classifier.infer(image, top_k=top_k)

                # 获取最高置信度的结果
                if predictions:
                    scene_type = predictions[0]["class_name"]
                    confidence = predictions[0]["confidence"]
                else:
                    scene_type = "unknown"
                    confidence = 0.0

            # 获取场景信息
            scene_info = SCENE_TYPES.get(scene_type, SCENE_TYPES["unknown"])

            return {
                "success": True,
                "scene_type": scene_type,
                "scene_name": scene_info["name"],
                "confidence": confidence,
                "recommended_tools": scene_info["recommended_tools"],
                "mock": False
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "scene_type": "unknown",
                "scene_name": SCENE_TYPES["unknown"]["name"],
                "confidence": 0.0,
                "recommended_tools": [],
                "mock": False
            }


# 创建全局模型服务实例
scene_model_service = SceneModelService()


# 创建 SceneService 包装类，提供简洁的API接口
class SceneService:
    """场景分类服务包装类"""

    @staticmethod
    def get_supported_scenes():
        """获取支持的场景类别"""
        model_loaded = scene_model_service.is_model_loaded

        scenes = [
            {
                "type": k,
                "name": v["name"],
                "description": v["description"]
            }
            for k, v in SCENE_TYPES.items()
            if k != "unknown"
        ]

        return {
            "supported_scenes": scenes,
            "total_classes": len(scenes),
            "model_loaded": model_loaded
        }

    @staticmethod
    def classify(image_base64: str) -> Dict:
        """
        分类场景

        Args:
            image_base64: base64编码的图片

        Returns:
            分类结果字典
        """
        return scene_model_service.classify_scene(image_base64)


# 创建服务实例
scene_service = SceneService()

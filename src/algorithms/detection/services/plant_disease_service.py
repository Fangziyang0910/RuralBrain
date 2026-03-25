"""
植物病害识别服务
基于百度飞桨2018年农作物病害数据集
支持10种植物（苹果、樱桃、葡萄、柑桔、桃、草莓、番茄、辣椒、玉米、马铃薯）
共61个分类（包含一般/严重程度）
"""
import os
import threading
from typing import Dict, List, Optional
from pathlib import Path

from algorithms.detection.services.onnx_cls import ONNXClassifier
from algorithms.detection.config import config


# 植物病害分类（根据百度飞桨2018年数据集，61个分类）
# 标签序号 0-60
PLANT_DISEASE_CLASSES = {
    0: {"name": "苹果（健康）", "crop": "苹果", "disease": "健康", "severity": None},
    1: {"name": "苹果黑星病（一般）", "crop": "苹果", "disease": "黑星病", "severity": "一般"},
    2: {"name": "苹果黑星病（严重）", "crop": "苹果", "disease": "黑星病", "severity": "严重"},
    3: {"name": "苹果灰斑病", "crop": "苹果", "disease": "灰斑病", "severity": None},
    4: {"name": "苹果雪松锈病（一般）", "crop": "苹果", "disease": "雪松锈病", "severity": "一般"},
    5: {"name": "苹果雪松锈病（严重）", "crop": "苹果", "disease": "雪松锈病", "severity": "严重"},
    6: {"name": "樱桃（健康）", "crop": "樱桃", "disease": "健康", "severity": None},
    7: {"name": "樱桃白粉病（一般）", "crop": "樱桃", "disease": "白粉病", "severity": "一般"},
    8: {"name": "樱桃白粉病（严重）", "crop": "樱桃", "disease": "白粉病", "severity": "严重"},
    9: {"name": "玉米（健康）", "crop": "玉米", "disease": "健康", "severity": None},
    10: {"name": "玉米灰斑病（一般）", "crop": "玉米", "disease": "灰斑病", "severity": "一般"},
    11: {"name": "玉米灰斑病（严重）", "crop": "玉米", "disease": "灰斑病", "severity": "严重"},
    12: {"name": "玉米锈病（一般）", "crop": "玉米", "disease": "锈病", "severity": "一般"},
    13: {"name": "玉米锈病（严重）", "crop": "玉米", "disease": "锈病", "severity": "严重"},
    14: {"name": "玉米叶斑病（一般）", "crop": "玉米", "disease": "叶斑病", "severity": "一般"},
    15: {"name": "玉米叶斑病（严重）", "crop": "玉米", "disease": "叶斑病", "severity": "严重"},
    16: {"name": "玉米花叶病毒病", "crop": "玉米", "disease": "花叶病毒病", "severity": None},
    17: {"name": "葡萄（健康）", "crop": "葡萄", "disease": "健康", "severity": None},
    18: {"name": "葡萄黑腐病（一般）", "crop": "葡萄", "disease": "黑腐病", "severity": "一般"},
    19: {"name": "葡萄黑腐病（严重）", "crop": "葡萄", "disease": "黑腐病", "severity": "严重"},
    20: {"name": "葡萄轮斑病（一般）", "crop": "葡萄", "disease": "轮斑病", "severity": "一般"},
    21: {"name": "葡萄轮斑病（严重）", "crop": "葡萄", "disease": "轮斑病", "severity": "严重"},
    22: {"name": "葡萄褐斑病（一般）", "crop": "葡萄", "disease": "褐斑病", "severity": "一般"},
    23: {"name": "葡萄褐斑病（严重）", "crop": "葡萄", "disease": "褐斑病", "severity": "严重"},
    24: {"name": "柑桔（健康）", "crop": "柑桔", "disease": "健康", "severity": None},
    25: {"name": "柑桔黄龙病（一般）", "crop": "柑桔", "disease": "黄龙病", "severity": "一般"},
    26: {"name": "柑桔黄龙病（严重）", "crop": "柑桔", "disease": "黄龙病", "severity": "严重"},
    27: {"name": "桃（健康）", "crop": "桃", "disease": "健康", "severity": None},
    28: {"name": "桃疮痂病（一般）", "crop": "桃", "disease": "疮痂病", "severity": "一般"},
    29: {"name": "桃疮痂病（严重）", "crop": "桃", "disease": "疮痂病", "severity": "严重"},
    30: {"name": "辣椒（健康）", "crop": "辣椒", "disease": "健康", "severity": None},
    31: {"name": "辣椒疮痂病（一般）", "crop": "辣椒", "disease": "疮痂病", "severity": "一般"},
    32: {"name": "辣椒疮痂病（严重）", "crop": "辣椒", "disease": "疮痂病", "severity": "严重"},
    33: {"name": "马铃薯（健康）", "crop": "马铃薯", "disease": "健康", "severity": None},
    34: {"name": "马铃薯早疫病（一般）", "crop": "马铃薯", "disease": "早疫病", "severity": "一般"},
    35: {"name": "马铃薯早疫病（严重）", "crop": "马铃薯", "disease": "早疫病", "severity": "严重"},
    36: {"name": "马铃薯晚疫病（一般）", "crop": "马铃薯", "disease": "晚疫病", "severity": "一般"},
    37: {"name": "马铃薯晚疫病（严重）", "crop": "马铃薯", "disease": "晚疫病", "severity": "严重"},
    38: {"name": "草莓（健康）", "crop": "草莓", "disease": "健康", "severity": None},
    39: {"name": "草莓叶枯病（一般）", "crop": "草莓", "disease": "叶枯病", "severity": "一般"},
    40: {"name": "草莓叶枯病（严重）", "crop": "草莓", "disease": "叶枯病", "severity": "严重"},
    41: {"name": "番茄（健康）", "crop": "番茄", "disease": "健康", "severity": None},
    42: {"name": "番茄白粉病（一般）", "crop": "番茄", "disease": "白粉病", "severity": "一般"},
    43: {"name": "番茄白粉病（严重）", "crop": "番茄", "disease": "白粉病", "severity": "严重"},
    44: {"name": "番茄疮痂病（一般）", "crop": "番茄", "disease": "疮痂病", "severity": "一般"},
    45: {"name": "番茄疮痂病（严重）", "crop": "番茄", "disease": "疮痂病", "severity": "严重"},
    46: {"name": "番茄早疫病（一般）", "crop": "番茄", "disease": "早疫病", "severity": "一般"},
    47: {"name": "番茄早疫病（严重）", "crop": "番茄", "disease": "早疫病", "severity": "严重"},
    48: {"name": "番茄晚疫病菌（一般）", "crop": "番茄", "disease": "晚疫病", "severity": "一般"},
    49: {"name": "番茄晚疫病菌（严重）", "crop": "番茄", "disease": "晚疫病", "severity": "严重"},
    50: {"name": "番茄叶霉病（一般）", "crop": "番茄", "disease": "叶霉病", "severity": "一般"},
    51: {"name": "番茄叶霉病（严重）", "crop": "番茄", "disease": "叶霉病", "severity": "严重"},
    52: {"name": "番茄斑点病（一般）", "crop": "番茄", "disease": "斑点病", "severity": "一般"},
    53: {"name": "番茄斑点病（严重）", "crop": "番茄", "disease": "斑点病", "severity": "严重"},
    54: {"name": "番茄斑枯病（一般）", "crop": "番茄", "disease": "斑枯病", "severity": "一般"},
    55: {"name": "番茄斑枯病（严重）", "crop": "番茄", "disease": "斑枯病", "severity": "严重"},
    56: {"name": "番茄红蜘蛛损伤（一般）", "crop": "番茄", "disease": "红蜘蛛损伤", "severity": "一般"},
    57: {"name": "番茄红蜘蛛损伤（严重）", "crop": "番茄", "disease": "红蜘蛛损伤", "severity": "严重"},
    58: {"name": "番茄黄化曲叶病毒病（一般）", "crop": "番茄", "disease": "黄化曲叶病毒病", "severity": "一般"},
    59: {"name": "番茄黄化曲叶病毒病（严重）", "crop": "番茄", "disease": "黄化曲叶病毒病", "severity": "严重"},
    60: {"name": "番茄花叶病毒病", "crop": "番茄", "disease": "花叶病毒病", "severity": None},
}


class PlantDiseaseModelService:
    """
    植物病害识别模型服务类
    线程安全，支持惰性初始化
    TODO: 等植物病害识别模型训练完成后启用
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
        classes_path = config.PLANT_DISEASE_CLASSES_PATH

        if not os.path.exists(classes_path):
            # 使用默认类别（61个分类）
            return [str(i) for i in range(61)]

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
                model_path = config.PLANT_DISEASE_MODEL_PATH

                # 检查模型文件是否存在
                if not os.path.exists(model_path):
                    print(f"[PlantDisease] 模型文件不存在: {model_path}")
                    print(f"[PlantDisease] 植物病害识别服务将以模拟模式运行")
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
                print(f"[PlantDisease] 已加载 {len(self._class_names)} 个病害类别")
                self._initialized = True
            except Exception as e:
                print(f"[PlantDisease] 模型初始化失败: {str(e)}")
                print(f"[PlantDisease] 植物病害识别服务将以模拟模式运行")
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

    def detect_disease(self, image_base64: str) -> Dict:
        """
        检测植物病害

        Args:
            image_base64: base64编码的图像字符串

        Returns:
            检测结果字典
        """
        self._initialize()

        # 如果模型未加载，返回模拟结果
        if not self._model_loaded:
            return {
                "success": True,
                "class_id": -1,
                "disease_name": "模型未加载",
                "crop": "未知",
                "disease": "未知",
                "severity": "未知",
                "confidence": 0.0,
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
                predictions, _ = self.classifier.infer(image, top_k=1)

                if predictions:
                    class_id = int(predictions[0]["class_name"])
                    confidence = predictions[0]["confidence"]
                else:
                    class_id = -1
                    confidence = 0.0

            # 获取病害信息
            disease_info = PLANT_DISEASE_CLASSES.get(class_id, {
                "name": "未知病害",
                "crop": "未知",
                "disease": "未知",
                "severity": "未知"
            })

            return {
                "success": True,
                "class_id": class_id,
                "disease_name": disease_info["name"],
                "crop": disease_info["crop"],
                "disease": disease_info["disease"],
                "severity": disease_info["severity"] or "无",
                "confidence": confidence,
                "mock": False
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "class_id": -1,
                "disease_name": "检测失败",
                "crop": "未知",
                "disease": "未知",
                "severity": "未知",
                "confidence": 0.0,
                "mock": False
            }


# 创建全局模型服务实例
plant_disease_model_service = PlantDiseaseModelService()


# 创建 PlantDiseaseService 包装类，提供简洁的API接口
class PlantDiseaseService:
    """植物病害识别服务包装类"""

    @staticmethod
    def get_supported_diseases():
        """获取支持的病害类别"""
        model_loaded = plant_disease_model_service.is_model_loaded

        diseases = [
            {
                "class_id": k,
                "name": v["name"],
                "crop": v["crop"],
                "disease": v["disease"],
                "severity": v["severity"] or "无"
            }
            for k, v in PLANT_DISEASE_CLASSES.items()
        ]

        return {
            "supported_diseases": diseases,
            "total_classes": len(diseases),
            "model_loaded": model_loaded,
            "crops": list(set(v["crop"] for v in PLANT_DISEASE_CLASSES.values()))
        }

    @staticmethod
    def detect(image_base64: str) -> Dict:
        """
        检测植物病害

        Args:
            image_base64: base64编码的图片

        Returns:
            检测结果字典
        """
        return plant_disease_model_service.detect_disease(image_base64)


# 创建服务实例
plant_disease_service = PlantDiseaseService()

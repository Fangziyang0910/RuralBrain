"""
疾病患处分类服务
使用 ONNX Runtime 进行图像分类识别
支持基于图片的疾病分类
"""
import cv2
import numpy as np
import base64
import os
import threading
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from algorithms.detection.services.onnx_cls import ONNXClassifier
from algorithms.detection.config import config


# 动物类型映射表
ANIMAL_TYPE_MAPPING = {
    "cow": ["cow_foot_and_mouth", "cow_healthy", "cow_lumpy"],
    "pig": ["pig_healthy", "pig_sick"],
    # 未来扩展
    # "chicken": ["chicken_healthy", "chicken_sick"],
    # "sheep": ["sheep_healthy", "sheep_sick"],
}

# 疾病中文名称映射
DISEASE_NAME_CN = {
    "cow_foot_and_mouth": "口蹄疫",
    "cow_healthy": "健康",
    "cow_lumpy": "牛结节性皮肤病",
    "pig_healthy": "健康",
    "pig_sick": "患病",
}


class DiseaseModelService:
    """
    疾病分类模型服务类
    线程安全，支持惰性初始化
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
        classes_path = config.DISEASE_CLASSES_PATH

        if not os.path.exists(classes_path):
            # 使用默认类别
            return ["cow_foot_and_mouth", "cow_healthy", "cow_lumpy",
                    "pig_healthy", "pig_sick"]

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
                model_path = config.DISEASE_MODEL_PATH

                # 检查模型文件是否存在
                if not os.path.exists(model_path):
                    print(f"[Disease] 模型文件不存在: {model_path}")
                    print(f"[Disease] 疾病检测服务将以模拟模式运行")
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
                print(f"[Disease] 已加载 {len(self._class_names)} 个疾病类别")
                self._initialized = True
            except Exception as e:
                print(f"[Disease] 模型初始化失败: {str(e)}")
                print(f"[Disease] 疾病检测服务将以模拟模式运行")
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

    def _base64_to_image(self, base64_str: str) -> np.ndarray:
        """将base64字符串转换为OpenCV图像"""
        img_data = base64.b64decode(base64_str)
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img

    def _image_to_base64(self, image: np.ndarray) -> str:
        """将OpenCV图像转换为base64字符串"""
        _, buffer = cv2.imencode('.jpg', image)
        img_str = base64.b64encode(buffer).decode('utf-8')
        return img_str

    def _detect_animal_type(self, class_name: str) -> Optional[str]:
        """根据类别名称推断动物类型"""
        for animal, diseases in ANIMAL_TYPE_MAPPING.items():
            if class_name in diseases:
                return animal
        return None

    def process_image_from_base64(
        self, image_base64: str, top_k: int = 3
    ) -> Tuple[List[Dict], str, Optional[str], Optional[str]]:
        """
        处理base64编码的图像并返回疾病分类结果

        Returns:
            Tuple[all_predictions, result_image_b64, primary_disease, animal_type]
        """
        self._initialize()

        # 转换base64图像
        image = self._base64_to_image(image_base64)
        if image is None:
            raise ValueError("无法解码图像数据")

        # 如果模型未加载，返回模拟结果
        if not self._model_loaded:
            # 模拟分类结果
            mock_predictions = [
                {
                    "class_id": 1,
                    "class_name": "cow_healthy",
                    "confidence": 0.75
                }
            ]
            result_image_b64 = self._image_to_base64(image)
            return mock_predictions, result_image_b64, "cow_healthy", "cow"

        # 使用线程锁保护推理过程
        with self._inference_lock:
            # 进行预测
            predictions, _ = self._classifier.infer(image, top_k=top_k)

            # 获取主要疾病（置信度最高的）
            primary_disease = predictions[0]["class_name"] if predictions else None

            # 推断动物类型
            animal_type = self._detect_animal_type(primary_disease) if primary_disease else None

            # 在图像上添加标签（可选）
            annotated_image = self._annotate_image(image, predictions[:3])
            result_image_b64 = self._image_to_base64(annotated_image)

        return predictions, result_image_b64, primary_disease, animal_type

    def _annotate_image(self, image: np.ndarray, predictions: List[Dict]) -> np.ndarray:
        """在图像上添加分类标签"""
        from PIL import Image, ImageDraw, ImageFont

        # 转换为 PIL 图像
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        draw = ImageDraw.Draw(pil_image)

        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        # 在图像左上角绘制分类结果
        y_offset = 10
        for pred in predictions:
            class_name = pred["class_name"]
            conf = pred["confidence"]

            # 检查是否在 Docker 环境
            is_docker = os.path.exists('/.dockerenv')
            label = class_name if is_docker else DISEASE_NAME_CN.get(class_name, class_name)
            text = f"{label}: {conf:.1%}"

            # 绘制背景
            bbox = draw.textbbox((0, 0), text, font=font) if font else (0, 0, 100, 20)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            draw.rectangle(
                [(10, y_offset), (10 + text_width + 10, y_offset + text_height + 10)],
                fill=(0, 0, 0, 180)
            )

            # 绘制文字
            if font:
                draw.text((15, y_offset + 5), text, fill=(255, 255, 255), font=font)

            y_offset += text_height + 20

        # 转回 OpenCV 格式
        annotated_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        return annotated_image

    def classify_diseases(self, image_base64: str, top_k: int = 3) -> Dict:
        """
        分类图像中的疾病

        Args:
            image_base64: base64编码的图像字符串
            top_k: 返回前 k 个预测结果

        Returns:
            分类结果字典
        """
        try:
            predictions, result_image, primary_disease, animal_type = \
                self.process_image_from_base64(image_base64, top_k)

            # 转换为API响应格式
            api_predictions = []
            for pred in predictions:
                api_predictions.append({
                    "name": pred["class_name"],
                    "confidence": pred["confidence"]
                })

            return {
                "success": True,
                "detections": api_predictions,
                "result_image": result_image,
                "primary_disease": primary_disease,
                "animal_type": animal_type
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "detections": [],
                "result_image": "",
                "message": f"疾病分类失败: {str(e)}"
            }


# 创建全局模型服务实例
disease_model_service = DiseaseModelService()


# 创建 DiseaseService 包装类，提供简洁的API接口
class DiseaseService:
    """疾病分类服务包装类"""

    @staticmethod
    def get_supported_diseases():
        """获取支持的疾病类别"""
        classes = disease_model_service.class_names
        model_loaded = disease_model_service.is_model_loaded

        return {
            "supported_diseases": classes,
            "total_classes": len(classes),
            "model_loaded": model_loaded,
            "animal_types": list(ANIMAL_TYPE_MAPPING.keys()),
            "disease_names_cn": {
                k: DISEASE_NAME_CN.get(k, k) for k in classes
            }
        }

    @staticmethod
    def detect(image_base64: str) -> Dict:
        """
        分类疾病

        Args:
            image_base64: base64编码的图片

        Returns:
            分类结果字典
        """
        return disease_model_service.classify_diseases(image_base64)

    @staticmethod
    def detect_detailed(image_base64: str, top_k: int = 3) -> Dict:
        """
        分类疾病（详细模式）

        Args:
            image_base64: base64编码的图片
            top_k: 返回前 k 个结果

        Returns:
            详细分类结果
        """
        return disease_model_service.classify_diseases(image_base64, top_k)


# 创建服务实例
disease_service = DiseaseService()

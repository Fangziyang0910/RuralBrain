"""
奶牛检测服务
从原始的 cow_detection 服务移植
"""
import cv2
import numpy as np
import base64
import os
import threading
from typing import Dict, List, Tuple, Optional
from ultralytics import YOLO

from detection.config import config


class CowModelService:
    """
    奶牛检测模型服务类
    线程安全，支持惰性初始化
    """

    def __init__(self):
        """初始化模型服务，但不立即加载模型"""
        self._model: Optional[YOLO] = None
        self._class_names: List[str] = []
        self._initialized: bool = False
        self._init_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    def _initialize(self):
        """线程安全的惰性初始化模型"""
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return

            try:
                model_path = config.COW_MODEL_PATH

                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"模型文件不存在: {model_path}")

                # 加载模型
                self._model = YOLO(model_path)

                # 获取模型自带的类别名称
                if hasattr(self._model, 'names') and self._model.names:
                    self._class_names = list(self._model.names.values())
                else:
                    self._class_names = [f"class_{i}" for i in range(10)]

                self._class_names = tuple(self._class_names)
                print(f"[Cow] 已加载 {len(self._class_names)} 个类别")
                self._initialized = True
            except Exception as e:
                raise RuntimeError(f"奶牛检测模型初始化失败: {str(e)}")

    @property
    def model(self) -> YOLO:
        """获取模型实例"""
        self._initialize()
        return self._model

    @property
    def class_names(self) -> Tuple[str, ...]:
        """获取类别名称列表"""
        self._initialize()
        return self._class_names

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

    def process_image_from_base64(
        self, image_base64: str, confidence_threshold: float = 0.5
    ) -> Tuple[List[Dict], str, List[Dict], Dict]:
        """
        处理base64编码的图像并返回检测结果和处理后的图像

        Returns:
            Tuple[api_detections, result_image_b64, detailed_detections, image_info]
        """
        self._initialize()

        # 转换base64图像
        image = self._base64_to_image(image_base64)
        if image is None:
            raise ValueError("无法解码图像数据")

        # 获取图像尺寸
        height, width = image.shape[:2]

        # 创建图像副本用于绘制
        result_image = image.copy()

        # 使用线程锁保护推理过程
        with self._inference_lock:
            # 进行预测
            results = self._model(result_image, conf=confidence_threshold, verbose=False)

            # 解析检测结果并绘制边界框
            detections = []
            class_counts = {}
            detailed_detections = []

            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                        # 计算牛只大小和中心点
                        cow_width = float(x2 - x1)
                        cow_height = float(y2 - y1)
                        center_x = float((x1 + x2) / 2)
                        center_y = float((y1 + y2) / 2)

                        # 获取类别名称
                        class_names = self._class_names
                        if class_id < len(class_names):
                            class_name = class_names[class_id]
                        else:
                            class_name = f"未知类别_{class_id}"

                        # 绘制边界框和标签
                        cv2.rectangle(result_image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                        label = f"{class_name}: {confidence:.2f}"
                        cv2.putText(result_image, label, (int(x1), int(y1) - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                        # 统计每个类别的数量
                        if class_name not in class_counts:
                            class_counts[class_name] = 0
                        class_counts[class_name] += 1

                        # 添加到详细检测结果
                        detailed_detection = {
                            "class_name": class_name,
                            "confidence": confidence,
                            "bbox": [float(x1), float(y1), float(x2), float(y2)],
                            "center": [center_x, center_y],
                            "size": {
                                "width": cow_width,
                                "height": cow_height,
                                "area": cow_width * cow_height
                            },
                            "relative_position": {
                                "x": center_x / width,
                                "y": center_y / height
                            }
                        }
                        detailed_detections.append(detailed_detection)

            # 转换为API期望的格式
            api_detections = []
            for class_name, count in class_counts.items():
                api_detections.append({
                    "name": class_name,
                    "count": count
                })

            # 添加图像尺寸信息
            image_info = {
                "width": width,
                "height": height,
                "total_cows": sum(class_counts.values())
            }

        # 将处理后的图像转换为base64
        result_image_b64 = self._image_to_base64(result_image)

        return api_detections, result_image_b64, detailed_detections, image_info

    def detect_cows_detailed(self, image_base64: str, confidence_threshold: float = 0.5) -> Dict:
        """
        检测图像中的牛只并返回详细信息

        Args:
            image_base64: base64编码的图像字符串
            confidence_threshold: 置信度阈值

        Returns:
            Dict: 包含详细检测信息的字典
        """
        api_detections, result_image_b64, detailed_detections, image_info = \
            self.process_image_from_base64(image_base64, confidence_threshold)

        return {
            "detections": api_detections,
            "detailed_detections": detailed_detections,
            "image_info": image_info,
            "result_image": result_image_b64
        }


# 创建全局模型服务实例
cow_model_service = CowModelService()


# 创建 CowService 包装类，提供简洁的API接口
class CowService:
    """奶牛检测服务包装类"""

    @staticmethod
    def get_supported_cows():
        """获取支持的奶牛品种"""
        return {
            "supported_cows": ["荷斯坦牛", "娟姗牛", "西门塔尔牛"],
            "total_classes": 3
        }

    @staticmethod
    def detect(image_base64: str) -> Dict:
        """
        检测奶牛

        Args:
            image_base64: base64编码的图片

        Returns:
            检测结果字典
        """
        try:
            api_detections, result_image, _, _ = cow_model_service.process_image_from_base64(image_base64)
            return {
                "success": True,
                "detections": api_detections,
                "result_image": result_image,
                "count": len(api_detections)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "detections": [],
                "count": 0
            }

    @staticmethod
    def detect_detailed(image_base64: str, conf_threshold: float = 0.5, iou_threshold: float = 0.45) -> Dict:
        """
        检测奶牛（详细模式）

        Args:
            image_base64: base64编码的图片
            conf_threshold: 置信度阈值
            iou_threshold: IOU阈值

        Returns:
            详细检测结果
        """
        try:
            result = cow_model_service.detect_cows_detailed(image_base64, conf_threshold)
            return {
                "success": True,
                **result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "detections": [],
                "detailed_detections": [],
                "count": 0
            }


# 创建服务实例
cow_service = CowService()

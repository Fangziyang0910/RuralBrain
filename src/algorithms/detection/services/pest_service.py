"""
病虫害检测服务
从原始的 pest_detection 服务移植
"""
import cv2
import numpy as np
import base64
import os
import threading
from typing import Dict, List, Tuple, Optional
from ultralytics import YOLO

from src.algorithms.detection.config import config


class PestModelService:
    """
    病虫害检测模型服务类
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
                model_path = config.PEST_MODEL_PATH
                classes_path = config.PEST_CLASSES_PATH

                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"模型文件不存在: {model_path}")
                if not os.path.exists(classes_path):
                    raise FileNotFoundError(f"类别文件不存在: {classes_path}")

                # 加载模型
                self._model = YOLO(model_path)

                # 加载类别
                class_names: List[str] = []
                if os.path.exists(classes_path):
                    encodings = ['utf-8', 'gbk', 'ansi']
                    for encoding in encodings:
                        try:
                            class_names = []
                            with open(classes_path, 'r', encoding=encoding) as f:
                                for line in f.readlines():
                                    line = line.strip()
                                    if line:
                                        parts = line.split()
                                        if len(parts) >= 2:
                                            # 查找中文字符
                                            last_chinese_pos = -1
                                            for i, char in enumerate(line):
                                                if '\u4e00' <= char <= '\u9fff':
                                                    last_chinese_pos = i
                                                    break

                                            if last_chinese_pos >= 0:
                                                chinese_name = line[last_chinese_pos:].strip()
                                                class_names.append(chinese_name)
                                            else:
                                                class_names.append(line)

                            if any(class_names):
                                print(f"[Pest] 使用编码 {encoding} 成功加载类别文件")
                                break
                        except UnicodeDecodeError:
                            continue
                    else:
                        print(f"[Pest] 警告: 无法正确解码类别文件，使用默认类别")
                        class_names = [f"class_{i}" for i in range(29)]
                else:
                    class_names = [f"class_{i}" for i in range(29)]

                self._class_names = tuple(class_names)
                print(f"[Pest] 已加载 {len(self._class_names)} 个类别")
                self._initialized = True
            except Exception as e:
                raise RuntimeError(f"病虫害检测模型初始化失败: {str(e)}")

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

    def predict(self, image: np.ndarray) -> Tuple[List[Dict], np.ndarray]:
        """使用YOLO模型进行预测（线程安全）"""
        self._initialize()
        image_copy = image.copy()

        try:
            with self._inference_lock:
                results = self._model(image_copy, verbose=False)
                annotated_image = results[0].plot()

                local_detections = []
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            confidence = float(box.conf[0])
                            if confidence < 0.3:
                                continue

                            class_id = int(box.cls[0])
                            class_names = self._class_names
                            if class_id < len(class_names):
                                class_name = class_names[class_id]
                                if not isinstance(class_name, str) or len(class_name.strip()) == 0:
                                    class_name = f"未知类别_{class_id}"
                            else:
                                class_name = f"未知类别_{class_id}"

                            local_detections.append({
                                "class_id": class_id,
                                "class_name": class_name,
                                "confidence": confidence
                            })

            # 统计每种害虫的数量
            pest_counts: Dict[str, int] = {}
            for det in local_detections:
                class_name = det["class_name"]
                if class_name in pest_counts:
                    pest_counts[class_name] += 1
                else:
                    pest_counts[class_name] = 1

            detections = [
                {"name": name, "count": count}
                for name, count in pest_counts.items()
            ]

            total_count = sum(pest_counts.values())
            print(f"[Pest] 检测到 {len(detections)} 种害虫，共 {total_count} 个目标")

            return detections, annotated_image
        except Exception as e:
            print(f"[Pest] 预测过程中出错: {str(e)}")
            return [], image.copy()

    def process_image_from_base64(self, base64_str: str) -> Tuple[List[Dict], str]:
        """处理base64编码的图像（线程安全、无状态）"""
        try:
            image_data = base64.b64decode(base64_str)
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                raise ValueError("无法解码图像数据")

            detections, annotated_image = self.predict(image)
            base64_image = self._image_to_base64(annotated_image)

            return detections, base64_image
        except Exception as e:
            raise RuntimeError(f"图像处理失败: {str(e)}")

    @staticmethod
    def _image_to_base64(image: np.ndarray) -> str:
        """将图像转换为base64编码字符串"""
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')


# 创建全局模型服务实例
pest_model_service = PestModelService()


# 创建 PestService 包装类，提供简洁的API接口
class PestService:
    """病虫害检测服务包装类"""

    @staticmethod
    def get_supported_pests():
        """获取支持的病虫害种类"""
        return {
            "supported_pests": [
                "稻飞虱", "稻纵卷叶螟", "二化螟", "三化螟",
                "稻瘟病", "纹枯病", "白叶枯病", "稻曲病"
            ],
            "total_classes": 29
        }

    @staticmethod
    def detect(image_base64: str) -> Dict:
        """
        检测病虫害

        Args:
            image_base64: base64编码的图片

        Returns:
            检测结果字典
        """
        try:
            detections, result_image = pest_model_service.process_image_from_base64(image_base64)
            return {
                "success": True,
                "detections": detections,
                "result_image": result_image,
                "count": len(detections)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "detections": [],
                "count": 0
            }


# 创建服务实例
pest_service = PestService()

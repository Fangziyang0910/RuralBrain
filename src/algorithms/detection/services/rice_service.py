"""
大米品种识别服务
使用 ONNX Runtime，无需 PyTorch 和 ultralytics
"""
import os
import base64
import threading
from typing import Dict, List, Any
import numpy as np
import cv2

from algorithms.detection.services.onnx_yolo import ONNXYOLODetector
from algorithms.detection.config import config


class RiceService:
    """
    大米品种识别服务（支持惰性加载）
    """

    def __init__(self):
        self.weights_path = config.RICE_MODEL_PATH
        self._detector = None
        self._initialized = False
        self._init_lock = threading.Lock()
        self.name_map = {
            '1': '糯米',
            '2': '丝苗米',
            '3': '泰国香米',
            '4': '五常大米',
            '5': '珍珠大米',
        }

    def _load_model(self):
        """惰性加载模型（线程安全）"""
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return

            if not os.path.exists(self.weights_path):
                raise FileNotFoundError(f'Model weights not found at {self.weights_path}')

            # 定义类别名称
            class_names = list(self.name_map.values())

            # 创建 ONNX YOLO 检测器
            self._detector = ONNXYOLODetector(
                model_path=self.weights_path,
                class_names=class_names,
                conf_threshold=0.3
            )

            self._initialized = True
            print(f"[Rice] 模型加载成功: {self.weights_path}")

    @property
    def detector(self):
        """获取检测器实例（惰性加载）"""
        self._load_model()
        return self._detector

    def _decode_base64_image(self, b64: str):
        try:
            image_data = base64.b64decode(b64)
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError('cv2.imdecode 返回 None')
            return img
        except Exception as e:
            raise ValueError(f'图片解码失败: {e}')

    def _parse_results(self, detections: List[Dict]) -> List[Dict[str, Any]]:
        """解析检测结果"""
        if not detections:
            return []

        class_counts = {}
        for det in detections:
            class_name = det['class_name']
            if class_name in class_counts:
                class_counts[class_name] += 1
            else:
                class_counts[class_name] = 1

        result = []
        for name, count in class_counts.items():
            result.append({
                'name': name,
                'count': count
            })

        return result

    def predict(self, image_base64: str) -> Dict[str, Any]:
        try:
            img = self._decode_base64_image(image_base64)
        except Exception as e:
            return {'success': False, 'message': str(e), 'detections': []}

        try:
            detections, annotated_image = self.detector.infer(img)
        except Exception as e:
            return {'success': False, 'message': f'模型推理失败: {e}', 'detections': []}

        parsed_detections = self._parse_results(detections)

        # 生成标注图片
        result_image_b64 = None
        try:
            success, buffer = cv2.imencode('.jpg', annotated_image)

            if success:
                result_image_b64 = base64.b64encode(buffer).decode('utf-8')
            else:
                print("[Rice] Warning: 图片内存编码失败")
        except Exception as e:
            print(f"[Rice] Warning: 生成标注图片时发生错误: {e}")

        return {
            'success': True,
            'detections': parsed_detections,
            'result_image': result_image_b64
        }

    @staticmethod
    def get_supported_rice_types():
        """获取支持的大米品种"""
        return {
            "supported_rice_types": [
                "糯米", "丝苗米", "泰国香米", "五常大米", "珍珠大米"
            ],
            "total_classes": 5
        }


# 创建全局服务实例
rice_service = RiceService()

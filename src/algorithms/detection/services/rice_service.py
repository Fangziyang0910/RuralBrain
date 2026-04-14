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
        # YOLO 模型返回 0-based 索引，使用整数键映射
        self.name_map = {
            0: '糯米',
            1: '丝苗米',
            2: '泰国香米',
            3: '五常大米',
            4: '珍珠大米',
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

            # YOLO11-seg 模型有 6 个类别（含 background）
            # 0: background, 1-5: 各类大米品种
            class_names = ['背景', '糯米', '丝苗米', '泰国香米', '五常大米', '珍珠大米']

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
        """解析检测结果（基础版本：只统计数量）"""
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

    def _parse_detailed_results(self, detections: List[Dict], image_height: int, image_width: int) -> List[Dict[str, Any]]:
        """解析详细检测结果（包含 bbox 和 confidence）"""
        if not detections:
            return []

        detailed_detections = []
        for det in detections:
            class_name = det['class_name']
            confidence = det['confidence']
            box = det['box']  # [x1, y1, x2, y2]

            # 跳过背景类别
            if class_name == '背景' or class_name == 'background':
                continue

            x1, y1, x2, y2 = box
            width = x2 - x1
            height = y2 - y1
            area = width * height
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            detailed_detections.append({
                'class_name': class_name,
                'confidence': confidence,
                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                'center': [float(center_x), float(center_y)],
                'size': {
                    'width': float(width),
                    'height': float(height),
                    'area': float(area)
                },
                'relative_position': {
                    'x': float(center_x / image_width),
                    'y': float(center_y / image_height)
                }
            })

        return detailed_detections

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

    def detect_detailed(self, image_base64: str) -> Dict[str, Any]:
        """详细检测方法，返回完整检测结果（包含 bbox 和 confidence）"""
        try:
            img = self._decode_base64_image(image_base64)
        except Exception as e:
            return {'success': False, 'message': str(e), 'detections': [], 'detailed_detections': []}

        image_height, image_width = img.shape[:2]

        try:
            detections, annotated_image = self.detector.infer(img)
        except Exception as e:
            return {'success': False, 'message': f'模型推理失败: {e}', 'detections': [], 'detailed_detections': []}

        # 解析基础统计结果
        parsed_detections = self._parse_results(detections)

        # 解析详细检测结果
        detailed_detections = self._parse_detailed_results(detections, image_height, image_width)

        # 计算总数
        total_count = sum(d['count'] for d in parsed_detections)

        # 计算平均置信度
        avg_confidence = 0.0
        if detailed_detections:
            confidences = [d['confidence'] for d in detailed_detections]
            avg_confidence = sum(confidences) / len(confidences)

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
            'detailed_detections': detailed_detections,
            'result_image': result_image_b64,
            'image_info': {
                'width': image_width,
                'height': image_height,
                'total_rice': total_count
            },
            'avg_confidence': avg_confidence
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

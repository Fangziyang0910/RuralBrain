"""
大米品种识别服务
从原始的 rice_detection 服务移植
"""
import os
import base64
import threading
from typing import Dict, List, Any
import numpy as np
import cv2

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

from app.core.config import settings


class RiceService:
    """
    大米品种识别服务（支持惰性加载）
    """

    def __init__(self):
        self.weights_path = settings.RICE_MODEL_PATH
        self._model = None
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

            if YOLO is None:
                raise RuntimeError('ultralytics YOLO 未安装或无法导入')
            if not os.path.exists(self.weights_path):
                raise FileNotFoundError(f'Model weights not found at {self.weights_path}')

            self._model = YOLO(self.weights_path)
            self._initialized = True
            print(f"[Rice] 模型加载成功: {self.weights_path}")

    @property
    def model(self):
        """获取模型实例（惰性加载）"""
        self._load_model()
        return self._model

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

    def _parse_results(self, results) -> List[Dict[str, Any]]:
        if results is None or len(results) == 0:
            return []
        res = results[0]

        if res.boxes is None or len(res.boxes) == 0:
            return []

        model_names = getattr(res, 'names', {})
        class_counts = {}

        for box in res.boxes:
            cls_id = int(box.cls[0].cpu().numpy())

            if cls_id in model_names:
                raw_name = model_names[cls_id]
            else:
                raw_name = str(cls_id)

            display_name = self.name_map.get(str(raw_name), raw_name)

            if display_name in class_counts:
                class_counts[display_name] += 1
            else:
                class_counts[display_name] = 1

        detections = []
        for name, count in class_counts.items():
            detections.append({
                'name': name,
                'count': count
            })

        return detections

    def predict(self, image_base64: str) -> Dict[str, Any]:
        try:
            img = self._decode_base64_image(image_base64)
        except Exception as e:
            return {'success': False, 'message': str(e), 'detections': []}

        try:
            results = self.model(img, verbose=False)
        except Exception as e:
            return {'success': False, 'message': f'模型推理失败: {e}', 'detections': []}

        detections = self._parse_results(results)

        # 生成标注图片
        result_image_b64 = None
        try:
            first_result = results[0]
            plot_img = first_result.plot()
            success, buffer = cv2.imencode('.jpg', plot_img)

            if success:
                result_image_b64 = base64.b64encode(buffer).decode('utf-8')
            else:
                print("[Rice] Warning: 图片内存编码失败")
        except Exception as e:
            print(f"[Rice] Warning: 生成标注图片时发生错误: {e}")

        return {
            'success': True,
            'detections': detections,
            'result_image': result_image_b64
        }


# 创建全局服务实例
rice_service = RiceService()

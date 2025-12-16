import os
import base64
from collections import Counter
from typing import List, Dict, Any

import numpy as np
import cv2

# 下面导入 ultralytics YOLO，如果你用其它库请替换对应加载和推理代码
try:
    from ultralytics import YOLO
except Exception:
    YOLO = None


# 兼容 Docker 和本地环境的导入
try:
    # Docker 环境：使用相对导入
    from app.core.config import settings
except ImportError:
    # 本地环境：使用绝对导入
    from src.algorithms.rice_detection.detector.app.core.config import settings


class RiceService:
    """
    单例服务：服务启动时加载模型，predict 使用内存图像，不写磁盘。
    """

    def __init__(self, weights_path: str = None, name_map: Dict[str, str] = None):
        self.weights_path = weights_path or settings.WEIGHTS_PATH_FL
        self.model = None
        self.name_map = name_map or {}
        self._load_model()

    def _load_model(self):
        if YOLO is None:
            # 延迟报错，便于单元测试或不使用 ultralytics 的环境
            raise RuntimeError('ultralytics YOLO 未安装或无法导入，请安装 ultralytics')
        if not os.path.exists(self.weights_path):
            raise FileNotFoundError(f'Model weights not found at {self.weights_path}')
        # 只在服务启动时加载一次
        self.model = YOLO(self.weights_path)

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
        # results: ultralytics Results list-like; 取第一个结果对象
        if results is None or len(results) == 0:
            return []
        res = results[0]
        
        # 如果没有检测框，返回空列表
        if res.boxes is None or len(res.boxes) == 0:
            return []
            
        # 获取模型类别名称
        model_names = getattr(res, 'names', {})
        
        # 按类别统计数量
        class_counts = {}
        
        # 遍历每个检测框
        for box in res.boxes:
            # 获取类别ID
            cls_id = int(box.cls[0].cpu().numpy())
            
            # 获取类别名称
            if cls_id in model_names:
                raw_name = model_names[cls_id]
            else:
                raw_name = str(cls_id)
                
            # 映射 name_map（例如将 '1' -> '糯米'）
            display_name = self.name_map.get(str(raw_name), raw_name)
            
            # 统计数量
            if display_name in class_counts:
                class_counts[display_name] += 1
            else:
                class_counts[display_name] = 1

        # 转换为检测结果格式
        detections = []
        for name, count in class_counts.items():
            detections.append({
                'name': name,
                'count': count
            })

        return detections

    def predict(self, image_base64: str) -> Dict[str, Any]:
        # 无状态：不读取或写入任何公共磁盘路径（除加载模型文件）
        try:
            img = self._decode_base64_image(image_base64)
        except Exception as e:
            return {'success': False, 'message': str(e), 'detections': []}

        # 推理：直接传 numpy 图像，ultralytics 支持
        try:
            results = self.model(img, verbose=False)
        except Exception as e:
            return {'success': False, 'message': f'模型推理失败: {e}', 'detections': []}

        # 解析文字结果 (保持你原有的辅助函数调用)
        detections = self._parse_results(results)

        # --- [新增] 生成标注图片逻辑 ---
        result_image_b64 = None
        try:
            # 1. 获取推理结果对象
            first_result = results[0]
            
            # 2. 调用 ultralytics 的 plot() 方法在图上画框
            # 返回的是一个 numpy 数组 (BGR格式)
            plot_img = first_result.plot()
            
            # 3. 将 numpy 图片在内存中编码为 jpg 格式
            # cv2.imencode 返回两个值: (bool_success, buffer)
            success, buffer = cv2.imencode('.jpg', plot_img)
            
            if success:
                # 4. 将 buffer 转为 Base64 字符串
                result_image_b64 = base64.b64encode(buffer).decode('utf-8')
            else:
                print("Warning: 图片内存编码失败")
                
        except Exception as e:
            # 画图失败不应导致整个请求报错，打印日志即可
            print(f"Warning: 生成标注图片时发生错误: {e}")

        # 返回结果，包含标注好的图片 Base64
        return {
            'success': True, 
            'detections': detections, 
            'result_image': result_image_b64
        }


# 单例：模块导入时创建（或你可以在 main 中显式创建）
_default_name_map = {
    '1': '糯米',
    '2': '丝苗米',
    '3': '泰国香米',
    '4': '五常大米',
    '5': '珍珠大米',
}

# 延迟实例化的工厂函数（避免导入时立即抛错）
_service_instance: RiceService = None

def get_rice_service() -> RiceService:
    global _service_instance
    if _service_instance is None:
        _service_instance = RiceService(name_map=_default_name_map)
    return _service_instance
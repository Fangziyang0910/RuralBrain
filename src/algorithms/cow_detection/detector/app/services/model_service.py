import cv2
import numpy as np
import base64
import os
import threading
from typing import Dict, List, Tuple, Optional
from ultralytics import YOLO

# 兼容 Docker 和本地环境的导入
try:
    # Docker 环境：使用相对导入
    from app.core.config import settings
    from app.schemas.detection import DetectionResult, VideoDetectionResult, BoundingBox
except ImportError:
    # 本地环境：使用绝对导入
    from src.algorithms.cow_detection.detector.app.core.config import settings
    from src.algorithms.cow_detection.detector.app.schemas.detection import DetectionResult, VideoDetectionResult, BoundingBox


class ModelService:
    """
    线程安全的牛检测模型服务类，负责YOLOv8模型的加载和推理
    
    设计原则：
    1. 模型加载使用线程锁保护，确保只初始化一次
    2. 推理过程使用线程锁保护，防止并发结果串线
    3. 类别名称为只读数据，初始化后不再修改
    4. 每次推理完全独立，不依赖任何跨请求状态
    """
    
    def __init__(self):
        """初始化模型服务，但不立即加载模型"""
        self._model: Optional[YOLO] = None
        self._class_names: List[str] = []
        self._initialized: bool = False
        # 线程锁：保护初始化过程
        self._init_lock = threading.Lock()
        # 线程锁：保护推理过程（YOLO模型可能不是线程安全的）
        self._inference_lock = threading.Lock()
    
    def _initialize(self):
        """
        线程安全的惰性初始化模型
        使用双重检查锁定模式确保只初始化一次
        """
        if self._initialized:
            return
        
        with self._init_lock:
            # 双重检查：防止多个线程同时通过第一个检查
            if self._initialized:
                return
            
            try:
                # 使用配置中的模型路径
                model_path = settings.MODEL_PATH
                
                # 验证文件是否存在
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"模型文件不存在: {model_path}")
                
                # 加载模型，使用本地模型，禁用自动下载
                self._model = YOLO(model_path, local=True)
                
                # 获取模型自带的类别名称
                if hasattr(self._model, 'names') and self._model.names:
                    self._class_names = list(self._model.names.values())
                else:
                    # 如果没有类别名称，使用默认类别
                    self._class_names = [f"class_{i}" for i in range(10)]  # 假设有10个类别
                
                # 将类别名称转为元组，变成不可变对象
                self._class_names = tuple(self._class_names)
                
                print(f"已加载 {len(self._class_names)} 个类别")
                self._initialized = True
            except Exception as e:
                raise RuntimeError(f"模型初始化失败: {str(e)}")
    
    @property
    def model(self) -> YOLO:
        """获取模型实例（只读属性）"""
        self._initialize()
        return self._model
    
    @property
    def class_names(self) -> Tuple[str, ...]:
        """获取类别名称列表（只读属性，返回元组确保不可变）"""
        self._initialize()
        return self._class_names
    
    def _base64_to_image(self, base64_str: str) -> np.ndarray:
        """将base64字符串转换为OpenCV图像"""
        # 解码base64字符串
        img_data = base64.b64decode(base64_str)
        # 将字节数据转换为numpy数组
        np_arr = np.frombuffer(img_data, np.uint8)
        # 解码为图像
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img
    
    def _image_to_base64(self, image: np.ndarray) -> str:
        """将OpenCV图像转换为base64字符串"""
        _, buffer = cv2.imencode('.jpg', image)
        img_str = base64.b64encode(buffer).decode('utf-8')
        return img_str
    
    def detect_cows(self, image_base64: str, confidence_threshold: float = 0.5) -> List[Dict]:
        """
        检测图像中的牛只
        
        Args:
            image_base64: base64编码的图像字符串
            confidence_threshold: 置信度阈值
            
        Returns:
            List[Dict]: 检测结果列表，每个元素包含name和count字段
        """
        # 使用新的process_image_from_base64方法
        api_detections, _, _, _ = self.process_image_from_base64(image_base64, confidence_threshold)
        return api_detections
    
    def detect_cows_detailed(self, image_base64: str, confidence_threshold: float = 0.5) -> Dict:
        """
        检测图像中的牛只并返回详细信息
        
        Args:
            image_base64: base64编码的图像字符串
            confidence_threshold: 置信度阈值
            
        Returns:
            Dict: 包含详细检测信息的字典
        """
        # 使用新的process_image_from_base64方法
        api_detections, result_image_b64, detailed_detections, image_info = self.process_image_from_base64(image_base64, confidence_threshold)
        
        return {
            "detections": api_detections,
            "detailed_detections": detailed_detections,
            "image_info": image_info,
            "result_image": result_image_b64
        }
    
    def detect_cows_in_video(self, video_base64: str, confidence_threshold: float = 0.5,
                            sample_rate: int = 10, model_name: Optional[str] = None) -> VideoDetectionResult:
        """检测视频中的牛"""
        import time
        start_time = time.time()
        
        # 惰性初始化（线程安全）
        self._initialize()
        
        # 保存临时视频文件
        temp_video_path = os.path.join(settings.UPLOAD_DIR, "temp_video.mp4")
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        try:
            with open(temp_video_path, "wb") as f:
                f.write(base64.b64decode(video_base64))
            
            # 读取视频
            cap = cv2.VideoCapture(temp_video_path)
            if not cap.isOpened():
                raise ValueError("无法打开视频文件")
                
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            processed_frames = 0
            total_detections = 0
            frame_detections = []
            
            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # 按采样率处理帧
                if frame_idx % sample_rate == 0:
                    # 使用线程锁保护推理过程
                    with self._inference_lock:
                        results = self._model(frame, conf=confidence_threshold, verbose=False)
                        
                        frame_detection = {
                            "frame_index": frame_idx,
                            "detections": []
                        }
                        
                        for result in results:
                            if result.boxes is not None:
                                for box in result.boxes:
                                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                    conf = float(box.conf[0])
                                    cls = int(box.cls[0])
                                    
                                    # 获取类别名称
                                    class_names = self._class_names
                                    if cls < len(class_names):
                                        class_name = class_names[cls]
                                    else:
                                        class_name = f"未知类别_{cls}"
                                    
                                    bbox = {
                                        "x1": float(x1),
                                        "y1": float(y1),
                                        "x2": float(x2),
                                        "y2": float(y2),
                                        "confidence": conf,
                                        "class_name": class_name,
                                        "class_id": cls
                                    }
                                    frame_detection["detections"].append(bbox)
                                    total_detections += 1
                    
                    frame_detections.append(frame_detection)
                    processed_frames += 1
                
                frame_idx += 1
            
            cap.release()
            
            processing_time = time.time() - start_time
            
            return VideoDetectionResult(
                video_path="base64_video",
                frame_count=frame_count,
                processed_frames=processed_frames,
                detections=frame_detections,
                total_detections=total_detections,
                processing_time=processing_time,
                model_name=model_name or "yolov8n"
            )
        except Exception as e:
            print(f"视频处理过程中出错: {str(e)}")
            # 返回默认值以避免服务崩溃
            return VideoDetectionResult(
                video_path="base64_video",
                frame_count=0,
                processed_frames=0,
                detections=[],
                total_detections=0,
                processing_time=time.time() - start_time,
                model_name=model_name or "yolov8n"
            )
        finally:
            # 删除临时文件
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
    
    def process_image_from_base64(self, image_base64: str, confidence_threshold: float = 0.5) -> Tuple[List[Dict], str]:
        """
        处理base64编码的图像并返回检测结果和处理后的图像
        
        Args:
            image_base64: base64编码的图像字符串
            confidence_threshold: 置信度阈值
            
        Returns:
            Tuple[List[Dict], str]: 检测结果列表(符合API期望的格式)和处理后的base64图像
        """
        # 惰性初始化（线程安全）
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
            class_counts = {}  # 用于统计每个类别的数量
            detailed_detections = []  # 存储详细的检测信息，类似cow_detection_tool
            
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        # 获取置信度
                        confidence = float(box.conf[0])
                        
                        # 获取类别ID
                        class_id = int(box.cls[0])
                        
                        # 获取边界框坐标
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
                        
                        # 添加到详细检测结果(类似cow_detection_tool)
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
                                "x": center_x / width,  # 相对x位置 (0-1)
                                "y": center_y / height  # 相对y位置 (0-1)
                            }
                        }
                        detailed_detections.append(detailed_detection)
                        
                        # 添加到检测结果(用于内部处理)
                        detections.append({
                            "class_name": class_name,
                            "confidence": confidence,
                            "bbox": {
                                "x1": float(x1),
                                "y1": float(y1),
                                "x2": float(x2),
                                "y2": float(y2)
                            },
                            "class_id": class_id
                        })
            
            # 转换为API期望的格式: 包含name和count的字典列表
            api_detections = []
            for class_name, count in class_counts.items():
                api_detections.append({
                    "name": class_name,
                    "count": count
                })
            
            # 添加图像尺寸信息到响应中
            image_info = {
                "width": width,
                "height": height,
                "total_cows": sum(class_counts.values())
            }
        
        # 将处理后的图像转换为base64
        result_image_b64 = self._image_to_base64(result_image)
        
        # 返回格式: [api_detections, detailed_detections, image_info, result_image_b64]
        # 但为了保持向后兼容，我们只返回api_detections和result_image_b64
        # 详细信息可以通过新的API端点获取
        return api_detections, result_image_b64, detailed_detections, image_info
    
    def get_available_models(self) -> List[Dict[str, any]]:
        """获取可用模型列表"""
        models = []
        
        # 添加默认模型
        if self._initialized:
            models.append({
                "name": "yolov8n",
                "path": settings.MODEL_PATH,
                "description": "YOLOv8 牛检测模型",
                "is_default": True,
                "size": "6MB",  # YOLOv8n模型大小
                "accuracy": "95%"  # 示例精度值
            })
        
        return models


# 创建全局模型服务实例
# 注意：虽然是全局单例，但已经通过以下机制保证线程安全：
# 1. 初始化使用双重检查锁定模式
# 2. 推理过程使用线程锁保护
# 3. 类别名称使用不可变元组
# 4. 所有方法内部只使用局部变量
model_service = ModelService()
import cv2
import numpy as np
import base64
import os
import threading
from typing import Dict, List, Tuple, Optional
from ultralytics import YOLO
from src.algorithms.pest_detection.detector.app.core.config import settings


class ModelService:
    """
    线程安全的模型服务类，负责YOLOv8模型的加载和推理
    
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
                # 使用配置中的相对路径
                # 注意：相对路径基于工作目录（运行 run.py 的目录）
                model_path = settings.MODEL_PATH
                classes_path = settings.CLASSES_PATH
                
                # 验证文件是否存在
                if not os.path.exists(model_path):
                    raise FileNotFoundError(f"模型文件不存在: {model_path}")
                if not os.path.exists(classes_path):
                    raise FileNotFoundError(f"类别文件不存在: {classes_path}")
                
                # 加载模型
                self._model = YOLO(model_path)
                
                # 加载类别，尝试不同编码
                class_names: List[str] = []
                if os.path.exists(classes_path):
                    encodings = ['utf-8', 'gbk', 'ansi']
                    for encoding in encodings:
                        try:
                            class_names = []  # 重置类别列表
                            with open(classes_path, 'r', encoding=encoding) as f:
                                for line in f.readlines():
                                    line = line.strip()
                                    if line:
                                        # 解析格式：英文名称 中文名称（可能有多个空格分隔）
                                        # 找到最后一个空格的位置，以此分隔中英文
                                        parts = line.split()
                                        if len(parts) >= 2:
                                            # 假设中文部分在最后，前面的都是英文部分
                                            # 查找最后一个中文字符的位置
                                            last_chinese_pos = -1
                                            for i, char in enumerate(line):
                                                if '\u4e00' <= char <= '\u9fff':  # 中文字符范围
                                                    last_chinese_pos = i
                                                    # 一旦找到中文字符，从这里开始就是中文部分
                                                    break
                                            
                                            if last_chinese_pos >= 0:
                                                # 提取中文名称
                                                chinese_name = line[last_chinese_pos:].strip()
                                                class_names.append(chinese_name)
                                            else:
                                                # 如果没有找到中文字符，使用整个行作为名称
                                                class_names.append(line)
                            
                            # 验证是否正确加载
                            if any(class_names):
                                print(f"使用编码 {encoding} 成功加载类别文件")
                                break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # 如果所有编码都失败，使用默认类别名称
                        print(f"警告: 无法正确解码类别文件，使用默认类别")
                        class_names = [f"class_{i}" for i in range(5)]  # 假设有5个类别
                else:
                    # 如果没有类别文件，使用默认类别
                    class_names = [f"class_{i}" for i in range(5)]  # 假设有5个类别
                
                # 将类别名称转为元组，变成不可变对象
                self._class_names = tuple(class_names)
                
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
    
    def predict(self, image: np.ndarray) -> Tuple[List[Dict], np.ndarray]:
        """
        使用YOLO模型进行预测（线程安全）
        
        该方法是完全无状态的：
        - 所有中间变量都是局部变量
        - 使用线程锁保护模型推理过程
        - 输入图像不会被修改（使用副本进行标注）
        - 返回的结果是全新创建的对象
        
        Args:
            image: 输入图像（BGR格式）
            
        Returns:
            Tuple[List[Dict], np.ndarray]: 检测结果（按名称统计数量）和标注后的图像
        """
        # 惰性初始化（线程安全）
        self._initialize()
        
        # 创建图像副本，确保不修改原始输入
        image_copy = image.copy()
        
        try:
            # 使用线程锁保护推理过程
            # YOLO模型的推理可能不是线程安全的，需要串行化
            with self._inference_lock:
                # 进行预测
                results = self._model(image_copy, verbose=False)  # 关闭详细输出
                
                # 在锁内获取标注后的图像（results[0].plot()可能修改内部状态）
                annotated_image = results[0].plot()
                
                # 在锁内解析所有检测结果，使用局部变量
                local_detections = []
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            # 获取置信度
                            confidence = float(box.conf[0])
                            if confidence < 0.3:  # 过滤低置信度结果
                                continue
                            
                            # 获取类别ID
                            class_id = int(box.cls[0])
                            
                            # 获取类别名称（使用只读属性）
                            class_names = self._class_names
                            if class_id < len(class_names):
                                class_name = class_names[class_id]
                                # 确保名称有效
                                if not isinstance(class_name, str) or len(class_name.strip()) == 0:
                                    class_name = f"未知类别_{class_id}"
                            else:
                                class_name = f"未知类别_{class_id}"
                            
                            local_detections.append({
                                "class_id": class_id,
                                "class_name": class_name,
                                "confidence": confidence
                            })
            
            # 以下操作在锁外进行，使用纯局部变量
            # 统计每种害虫的数量（使用局部字典）
            pest_counts: Dict[str, int] = {}
            for det in local_detections:
                class_name = det["class_name"]
                if class_name in pest_counts:
                    pest_counts[class_name] += 1
                else:
                    pest_counts[class_name] = 1
            
            # 转换为列表格式（创建全新的列表对象）
            detections = [
                {
                    "name": name,
                    "count": count
                }
                for name, count in pest_counts.items()
            ]
            
            total_count = sum(pest_counts.values())
            print(f"检测到 {len(detections)} 种害虫，共 {total_count} 个目标")
            if detections:
                for det in detections:
                    print(f"  {det['name']}: {det['count']}个")
            else:
                print("未检测到任何目标")
            
            return detections, annotated_image
        except Exception as e:
            print(f"预测过程中出错: {str(e)}")
            # 返回默认值以避免服务崩溃
            return [], image.copy()
    
    def process_image_from_base64(self, base64_str: str) -> Tuple[List[Dict], str]:
        """
        处理base64编码的图像（线程安全、无状态）
        
        该方法是完全无状态的：
        - 所有变量都是局部变量
        - 不依赖任何跨请求状态
        - 输入什么就输出什么，每次调用完全独立
        
        Args:
            base64_str: base64编码的图像字符串
            
        Returns:
            Tuple[List[Dict], str]: 检测结果和标注后的图像base64字符串
        """
        try:
            # 解码base64图像（局部变量）
            image_data = base64.b64decode(base64_str)
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("无法解码图像数据")
            
            # 进行预测（线程安全）
            detections, annotated_image = self.predict(image)
            
            # 将标注后的图像转换为base64（局部变量）
            base64_image = self._image_to_base64(annotated_image)
            
            return detections, base64_image
        except Exception as e:
            raise RuntimeError(f"图像处理失败: {str(e)}")
    
    @staticmethod
    def _image_to_base64(image: np.ndarray) -> str:
        """
        将图像转换为base64编码字符串（静态方法，无状态）
        
        Args:
            image: BGR格式的图像
            
        Returns:
            str: base64编码的图像字符串
        """
        # 转换为JPG格式（所有操作都是局部的）
        _, buffer = cv2.imencode('.jpg', image)
        # 转换为base64
        return base64.b64encode(buffer).decode('utf-8')
    
    # 保留旧方法名以保持向后兼容
    def image_to_base64(self, image: np.ndarray) -> str:
        """向后兼容的包装方法"""
        return self._image_to_base64(image)


# 创建全局模型服务实例
# 注意：虽然是全局单例，但已经通过以下机制保证线程安全：
# 1. 初始化使用双重检查锁定模式
# 2. 推理过程使用线程锁保护
# 3. 类别名称使用不可变元组
# 4. 所有方法内部只使用局部变量
model_service = ModelService()
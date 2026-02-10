"""
ONNX Runtime 推理引擎
用于替代 YOLO 进行轻量级模型推理
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("onnxruntime 未安装，ONNX 推理不可用")


class ONNXModel:
    """ONNX 模型推理器"""

    def __init__(self, model_path: str, input_size: int = 640):
        """
        初始化 ONNX 模型

        Args:
            model_path: ONNX 模型文件路径
            input_size: 输入图像尺寸
        """
        if not ONNX_AVAILABLE:
            raise RuntimeError("onnxruntime 未安装")

        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        self.model_path = str(model_path)
        self.input_size = input_size

        # 获取执行提供者（CPU/GPU）
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        available_providers = ort.get_available_providers()
        # 使用可用的提供者
        self.providers = [p for p in providers if p in available_providers]

        # 加载模型
        self.session = ort.InferenceSession(
            self.model_path,
            providers=self.providers
        )

        # 获取输入输出信息
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [o.name for o in self.session.get_outputs()]

        # 获取输入形状
        input_shape = self.session.get_inputs()[0].shape
        self.batch_size = input_shape[0]
        self.input_height = input_shape[2]
        self.input_width = input_shape[3]

        logger.info(f"ONNX 模型加载成功: {model_path}")
        logger.info(f"执行提供者: {self.session.get_providers()}")

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        预处理图像

        Args:
            image: BGR 格式图像 (H, W, C)

        Returns:
            预处理后的张量 (1, 3, H, W)
        """
        # 调整大小
        resized = cv2.resize(image, (self.input_width, self.input_height))

        # 归一化到 [0, 1]
        normalized = resized.astype(np.float32) / 255.0

        # 转换为 CHW 格式
        transposed = normalized.transpose(2, 0, 1)

        # 添加批次维度
        batched = np.expand_dims(transposed, axis=0)

        return batched

    def postprocess_detection(
        self,
        outputs: List[np.ndarray],
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45
    ) -> Tuple[List[Dict], int]:
        """
        后处理检测输出

        Args:
            outputs: 模型输出
            conf_threshold: 置信度阈值
            iou_threshold: IOU 阈值（NMS）

        Returns:
            (检测结果列表, 检测到的目标总数)
        """
        # YOLOv8 输出格式: (1, 84, 8400) 或 (1, num_classes+4, 8400)
        # 84 = 4 (bbox) + 80 (classes)
        output = outputs[0]  # (1, num_detections, num_classes+4)

        # 转置为 (8400, 84)
        detections = output[0].transpose()

        # 提取边界框和类别分数
        boxes = detections[:, :4]  # (x, y, w, h) 格式
        scores = detections[:, 4:]  # 类别分数

        # 找到每个检测的最大类别和分数
        class_ids = np.argmax(scores, axis=1)
        confidences = np.max(scores, axis=1)

        # 过滤低置信度检测
        mask = confidences > conf_threshold
        boxes = boxes[mask]
        class_ids = class_ids[mask]
        confidences = confidences[mask]

        # 应用 NMS
        indices = cv2.dnn.NMSBoxes(
            bboxes=boxes.tolist(),
            scores=confidences.tolist(),
            score_threshold=conf_threshold,
            nms_threshold=iou_threshold
        )

        # 统计检测结果
        class_counts: Dict[str, int] = {}

        if len(indices) > 0:
            for i in indices.flatten():
                class_id = int(class_ids[i])
                confidence = float(confidences[i])

                # 类别计数
                class_name = f"class_{class_id}"
                class_counts[class_name] = class_counts.get(class_name, 0) + 1

        # 转换为 API 格式
        detections_list = [
            {"name": name, "count": count}
            for name, count in class_counts.items()
        ]

        return detections_list, len(indices) if len(indices) > 0 else 0

    def infer(self, image: np.ndarray) -> List[np.ndarray]:
        """
        执行推理

        Args:
            image: 输入图像 (H, W, C) BGR 格式

        Returns:
            模型输出列表
        """
        # 预处理
        input_tensor = self.preprocess(image)

        # 推理
        outputs = self.session.run(
            self.output_names,
            {self.input_name: input_tensor}
        )

        return outputs


def create_onnx_model(model_path: str, input_size: int = 640) -> ONNXModel:
    """
    创建 ONNX 模型实例的工厂函数

    Args:
        model_path: ONNX 模型文件路径
        input_size: 输入图像尺寸

    Returns:
        ONNXModel 实例
    """
    return ONNXModel(model_path, input_size)

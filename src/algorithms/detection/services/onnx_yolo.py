"""
ONNX YOLO 推理引擎
直接使用 ONNX Runtime，无需 PyTorch 和 ultralytics
"""
import cv2
import numpy as np
import onnxruntime as ort
from typing import List, Dict, Tuple, Optional
import os


class ONNXYOLODetector:
    """
    基于 ONNX Runtime 的 YOLO 检测器
    支持 YOLOv8/YOLOv10 等导出的 ONNX 模型
    """

    def __init__(self, model_path: str, class_names: List[str], conf_threshold: float = 0.3):
        """
        初始化 ONNX YOLO 检测器

        Args:
            model_path: ONNX 模型路径
            class_names: 类别名称列表
            conf_threshold: 置信度阈值
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        # 配置 ONNX Runtime
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)

        # 获取输入输出信息
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self.output_names = [o.name for o in self.session.get_outputs()]

        self.class_names = class_names
        self.conf_threshold = conf_threshold

        # 获取输入尺寸
        self.input_height = self.input_shape[2] if len(self.input_shape) == 4 else 640
        self.input_width = self.input_shape[3] if len(self.input_shape) == 4 else 640

        print(f"[ONNX YOLO] 模型加载成功: {model_path}")
        print(f"[ONNX YOLO] 输入: {self.input_name} {self.input_shape}")
        print(f"[ONNX YOLO] 输出: {self.output_names}")
        print(f"[ONNX YOLO] 类别: {len(class_names)} 个")
        print(f"[ONNX YOLO] 提供者: {self.session.get_providers()}")

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        预处理图像

        Args:
            image: BGR 格式图像

        Returns:
            预处理后的图像数组
        """
        # Resize 到模型输入尺寸
        resized = cv2.resize(image, (self.input_width, self.input_height))

        # 归一化到 [0, 1]
        normalized = resized.astype(np.float32) / 255.0

        # HWC -> CHW
        transposed = normalized.transpose(2, 0, 1)

        # 添加 batch 维度
        batched = np.expand_dims(transposed, axis=0)

        return batched

    def postprocess(self, outputs: List[np.ndarray], original_shape: Tuple[int, int]) -> Tuple[List[Dict], np.ndarray]:
        """
        后处理模型输出（包含 NMS）

        Args:
            outputs: 模型输出列表
            original_shape: 原始图像尺寸 (height, width)

        Returns:
            (检测结果列表, 原始图像)
        """
        # YOLOv8/YOLOv10 输出格式: [batch, 84, 8400] 或 [batch, num_classes+4, anchors]
        # 其中 84 = 4(box) + 80(classes)
        output = outputs[0]

        # 解析输出
        predictions = np.squeeze(output).T  # [8400, 84]

        # 提取边界框和类别分数
        boxes = predictions[:, :4]      # [x_center, y_center, width, height]
        scores = predictions[:, 4:]     # [class1_score, class2_score, ...]

        # 找到每个锚点的最高分数类别
        class_ids = np.argmax(scores, axis=1)
        confidences = np.max(scores, axis=1)

        # 转换边界框格式: [x_center, y_center, width, height] -> [x1, y1, x2, y2]
        x_center = boxes[:, 0]
        y_center = boxes[:, 1]
        width = boxes[:, 2]
        height = boxes[:, 3]

        x1 = x_center - width / 2
        y1 = y_center - height / 2
        x2 = x_center + width / 2
        y2 = y_center + height / 2

        # 缩放到原始图像尺寸
        orig_h, orig_w = original_shape
        scale_x = orig_w / self.input_width
        scale_y = orig_h / self.input_height

        x1 = x1 * scale_x
        y1 = y1 * scale_y
        x2 = x2 * scale_x
        y2 = y2 * scale_y

        # 应用 NMS 过滤重复检测
        # 构造边界框列表: [[x1, y1, x2, y2], ...]
        bbox_list = []
        for i in range(len(x1)):
            bbox_list.append([float(x1[i]), float(y1[i]), float(x2[i]), float(y2[i])])

        indices = cv2.dnn.NMSBoxes(
            bboxes=bbox_list,
            scores=confidences.tolist(),
            score_threshold=self.conf_threshold,
            nms_threshold=0.45  # IOU 阈值
        )

        # 组装结果（使用 NMS 后的索引）
        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                class_id = int(class_ids[i])
                if class_id < len(self.class_names):
                    class_name = self.class_names[class_id]
                else:
                    class_name = f"class_{class_id}"

                detections.append({
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": float(confidences[i]),
                    "box": [float(x1[i]), float(y1[i]), float(x2[i]), float(y2[i])]
                })

        return detections, boxes.shape if len(boxes) > 0 else np.array([])

    def infer(self, image: np.ndarray) -> Tuple[List[Dict], np.ndarray]:
        """
        推理

        Args:
            image: BGR 格式图像

        Returns:
            (检测结果列表, 标注后的图像)
        """
        original_shape = image.shape[:2]

        # 预处理
        input_data = self.preprocess(image)

        # 推理
        outputs = self.session.run(self.output_names, {self.input_name: input_data})

        # 后处理
        detections, _ = self.postprocess(outputs, original_shape)

        # 绘制结果
        annotated_image = self.draw_detections(image.copy(), detections)

        return detections, annotated_image

    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        在图像上绘制检测结果

        Args:
            image: 原始图像
            detections: 检测结果列表

        Returns:
            标注后的图像
        """
        for det in detections:
            box = det["box"]
            conf = det["confidence"]
            class_name = det["class_name"]

            x1, y1, x2, y2 = map(int, box)

            # 绘制边界框
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 绘制标签
            label = f"{class_name} {conf:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(image, (x1, y1 - label_size[1] - 5),
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            cv2.putText(image, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

        return image

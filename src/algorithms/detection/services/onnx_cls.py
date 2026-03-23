"""
ONNX 分类推理引擎
用于 YOLOv8 Classification 模型
"""
import cv2
import numpy as np
import onnxruntime as ort
from typing import List, Dict, Tuple, Optional
import os


class ONNXClassifier:
    """
    基于 ONNX Runtime 的图像分类器
    支持 YOLOv8 分类模型导出的 ONNX 格式
    """

    def __init__(self, model_path: str, class_names: List[str]):
        """
        初始化 ONNX 分类器

        Args:
            model_path: ONNX 模型路径
            class_names: 类别名称列表
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        # 配置 ONNX Runtime
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)

        # 获取输入输出信息
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self.output_name = self.session.get_outputs()[0].name

        self.class_names = class_names

        # 获取输入尺寸
        # YOLOv8 cls 输入格式: [batch, 3, height, width]
        if len(self.input_shape) == 4:
            self.input_height = self.input_shape[2]
            self.input_width = self.input_shape[3]
        else:
            self.input_height = 224
            self.input_width = 224

        print(f"[ONNX Cls] 模型加载成功: {model_path}")
        print(f"[ONNX Cls] 输入: {self.input_name} {self.input_shape}")
        print(f"[ONNX Cls] 输出: {self.output_name}")
        print(f"[ONNX Cls] 类别: {len(class_names)} 个")
        print(f"[ONNX Cls] 提供者: {self.session.get_providers()}")

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        预处理图像

        YOLOv8 cls 预处理:
        1. Resize 到 input_size
        2. BGR -> RGB
        3. 归一化到 [0, 1]
        4. HWC -> CHW
        5. 添加 batch 维度

        Args:
            image: BGR 格式图像

        Returns:
            预处理后的图像数组
        """
        # Resize
        resized = cv2.resize(image, (self.input_width, self.input_height))

        # BGR -> RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # 归一化到 [0, 1]
        normalized = rgb.astype(np.float32) / 255.0

        # HWC -> CHW
        transposed = normalized.transpose(2, 0, 1)

        # 添加 batch 维度
        batched = np.expand_dims(transposed, axis=0)

        return batched

    def postprocess(self, outputs: np.ndarray) -> List[Dict]:
        """
        后处理模型输出

        YOLOv8 cls 输出: [batch, num_classes] 的 logits

        Args:
            outputs: 模型输出

        Returns:
            分类结果列表 [{"class_id": int, "class_name": str, "confidence": float}, ...]
        """
        # outputs shape: [1, num_classes]
        scores = outputs[0]  # 移除 batch 维度

        # 应用 softmax 获得概率
        exp_scores = np.exp(scores - np.max(scores))
        probabilities = exp_scores / np.sum(exp_scores)

        # 构建结果
        results = []
        for idx, (class_name, prob) in enumerate(zip(self.class_names, probabilities)):
            results.append({
                "class_id": idx,
                "class_name": class_name,
                "confidence": float(prob)
            })

        # 按置信度降序排序
        results.sort(key=lambda x: x["confidence"], reverse=True)

        return results

    def infer(self, image: np.ndarray, top_k: int = None) -> Tuple[List[Dict], np.ndarray]:
        """
        推理

        Args:
            image: BGR 格式图像
            top_k: 返回前 k 个结果，None 返回全部

        Returns:
            (分类结果列表, 原始logits)
        """
        # 预处理
        input_data = self.preprocess(image)

        # 推理
        outputs = self.session.run([self.output_name], {self.input_name: input_data})

        # 后处理
        results = self.postprocess(outputs[0])

        if top_k is not None:
            results = results[:top_k]

        return results, outputs[0]

    def predict(self, image: np.ndarray) -> Dict:
        """
        预测单个图像的主要类别

        Args:
            image: BGR 格式图像

        Returns:
            {"class_id": int, "class_name": str, "confidence": float}
        """
        results, _ = self.infer(image, top_k=1)
        return results[0] if results else None

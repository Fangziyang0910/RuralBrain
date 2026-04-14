"""
ONNX YOLO 推理引擎
直接使用 ONNX Runtime，无需 PyTorch 和 ultralytics
"""
import cv2
import numpy as np
import onnxruntime as ort
from typing import List, Dict, Tuple, Optional
import os
from PIL import Image, ImageDraw, ImageFont


# 检测是否为 Docker 环境
def is_docker_environment() -> bool:
    """检测是否在 Docker 容器中运行"""
    # 方法1: 检查 /.dockerenv 文件是否存在
    if os.path.exists('/.dockerenv'):
        return True
    # 方法2: 检查 /proc/1/cgroup 文件中是否包含 docker
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read()
    except (FileNotFoundError, IOError):
        pass
    # 方法3: 检查环境变量
    if os.getenv('DOCKER', '').lower() in ('true', '1', 'yes'):
        return True
    return False


# 中文类别到英文的映射表（用于 Docker 环境中文字体不可用的情况）
# 使用模型原始的英文名称，确保准确性
CHINESE_TO_ENGLISH = {
    # 病虫害类别（完整29类）- 使用模型原始英文名
    "瓜实蝇": "Melon fly",
    "小菜蛾": "Diamondback moth",
    "斑潜蝇": "Leafminer fly",
    "侧多食跗线螨": "Tarsonemid mite",
    "稻粉虱": "Rice whitefly",
    "白粉虱": "Rice whitefly",
    "荔枝蒂蛀虫": "Litchi fruit borer",
    "荔枝蝽": "Litchi stink bug",
    "荔枝瘿螨": "Eriophyes litchii",
    "甘蔗螟虫": "Sugarcane borer",
    "茶小绿叶蝉": "Tea green leafhopper",
    "福寿螺": "Apple snail",
    "小象甲": "Maize weevil",
    "烟粉虱": "Tobacco whitefly",
    "稻纵卷叶螟": "rice leaf roller",
    "大螟": "paddy stem maggot",
    "二化螟": "asian rice borer",
    "稻飞虱": "brown plant hopper",
    "玉米螟": "corn borer",
    "草地贪夜蛾": "army worm",
    "蚜虫": "aphids",
    "黄曲条跳甲": "flea beetle",
    "甜菜夜蛾": "beet army worm",
    "蓟马": "Thrips",
    "菜青虫": "Pieris canidia",
    "柑桔红蜘蛛": "Panonchus citri McGregor",
    "柑桔锈蜘蛛": "Phyllocoptes oleiverus ashmead",
    "桔小实蝇": "Dacus dorsalis(Hendel)",
    "斜纹夜蛾": "Prodenia litura",
    "柑桔潜叶蛾": "Phyllocnistis citrella Stainton",

    # 备用类别名称（用于部分匹配）
    "螟": "borer",
    "飞虱": "hopper",
    "纵卷叶螟": "rice leaf roller",
    "褐飞虱": "brown plant hopper",
    "白背飞虱": "hopper",
    "灰飞虱": "hopper",
    "白叶枯": "blight",
    "纹枯": "blight",
    "稻纵": "rice leaf roller",

    # 大米品种类别 - 使用英文名
    "糯米": "Sticky rice",
    "丝苗米": "Siam rice",
    "泰国香米": "Jasmine rice",
    "五常大米": "Wuchang rice",
    "珍珠大米": "Pearl rice",
    "背景": "background",

    # 奶牛类别
    "cow": "cow",

    # 通用类别
    "牛": "cow",
    "害虫": "pest",
    "稻米": "rice",
}


def chinese_to_english(text: str) -> str:
    """
    将中文类别名称转换为英文（或保持英文名称）

    Args:
        text: 类别名称（可能是中文或英文）

    Returns:
        转换后的名称（中文转英文，英文保持不变）
    """
    # 如果是英文名称，直接返回
    if not any('\u4e00' <= char <= '\u9fff' for char in text):
        return text

    # 尝试从映射表查找
    if text in CHINESE_TO_ENGLISH:
        return CHINESE_TO_ENGLISH[text]

    # 如果映射表中没有，尝试部分匹配
    for chinese, english in CHINESE_TO_ENGLISH.items():
        if chinese in text:
            # 替换匹配的部分
            return text.replace(chinese, english)

    # 如果都没有匹配，返回原文本
    return text


class ONNXYOLODetector:
    """
    基于 ONNX Runtime 的 YOLO 检测器
    支持 YOLOv8/YOLOv10 等导出的 ONNX 模型
    """

    def __init__(self, model_path: str, class_names: List[str], conf_threshold: float = 0.7):
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
        # BGR 转 RGB（重要！YOLO 模型训练时使用 RGB 格式）
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Resize 到模型输入尺寸
        resized = cv2.resize(image_rgb, (self.input_width, self.input_height))

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
        # YOLO11-seg 输出格式: [batch, num_classes+4, anchors] + mask outputs
        output = outputs[0]

        # 解析输出
        predictions = np.squeeze(output).T  # [8400, 84] 或 [anchors, 4+classes]

        # 判断输出格式
        if predictions.shape[0] == 8400 and predictions.shape[1] == 84:
            # YOLOv8 格式: [anchors, 84] = [anchors, 4 + 80(classes)]
            boxes = predictions[:, :4]      # [x_center, y_center, width, height]
            scores = predictions[:, 4:]     # [class1_score, class2_score, ...]
            num_classes = predictions.shape[1] - 4
        elif predictions.shape[0] == 8400 and predictions.shape[1] == 42:  # YOLO11-seg with 6 classes
            # YOLO11-seg 格式: [anchors, 42] = [anchors, 4(box) + 6(class_scores) + 32(mask_params)]
            boxes = predictions[:, :4]
            scores = predictions[:, 4:10]  # 6 个类别分数
            num_classes = 6
        elif predictions.shape[0] == 8400 and predictions.shape[1] in [5, 6, 38]:  # YOLO11-seg
            # YOLO11-seg 格式: [anchors, 5] 或 [anchors, 6] 或 [anchors, 38]
            # 这里的 5 = 4(box) + 1(conf) 或 4(box) + 2(classes) 或 4(box) + 34(mask_params)
            boxes = predictions[:, :4]
            scores = predictions[:, 4:]
            num_classes = predictions.shape[1] - 4
        else:
            # 未知格式，假设 YOLOv8
            boxes = predictions[:, :4]
            scores = predictions[:, 4:]
            num_classes = predictions.shape[1] - 4 if predictions.shape[1] > 4 else 1

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

        # 调整 NMS 阈值提高召回率（从 0.45 调到 0.6）
        # 对于密集场景（如很多 cows 或 rice），需要更高的 NMS 阈值
        indices = cv2.dnn.NMSBoxes(
            bboxes=bbox_list,
            scores=confidences.tolist(),
            score_threshold=self.conf_threshold,  # 恢复原始分数阈值
            nms_threshold=0.80  # IOU 阈值，更宽松，保留更多重叠检测
        )

        # 组装结果（使用 NMS 后的索引）
        detections = []
        if len(indices) > 0:
            # YOLO11-seg: 跳过 mask 输出（output1），只使用 output0
            # YOLOv8: 只有一个输出
            if len(outputs) > 1:
                print(f"[ONNX YOLO] 警告: 检测到 {len(outputs)} 个输出，只使用第一个")

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
        在图像上绘制检测结果（使用英文标签）

        Args:
            image: 原始图像
            detections: 检测结果列表

        Returns:
            标注后的图像
        """
        # 复制图像以避免修改原图
        annotated_image = image.copy()

        # 检测是否在 Docker 环境中，Docker 环境强制使用英文
        use_english = is_docker_environment()
        if use_english:
            print("[ONNX YOLO] 检测到 Docker 环境，使用英文标签")

        for det in detections:
            box = det["box"]
            conf = det["confidence"]
            class_name = det["class_name"]

            x1, y1, x2, y2 = map(int, box)

            # 绘制边界框（绿色）
            cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 在 Docker 环境中，强制使用英文
            if use_english:
                label_name = chinese_to_english(class_name)
            else:
                label_name = class_name

            # 构建标签文字
            label = f"{label_name} {conf:.2f}"

            # 使用 OpenCV 绘制文字（支持字体大小调整）
            # HersheySimplex 是 OpenCV 内置的字体，支持 scale 参数
            font_scale = 0.5  # 字体大小
            font_thickness = 1  # 字体粗细
            font = cv2.FONT_HERSHEY_SIMPLEX

            # 获取文字大小
            (text_width, text_height), baseline = cv2.getTextSize(
                label, font, font_scale, font_thickness
            )

            # 计算标签位置（在边界框上方）
            label_y = y1 - text_height - 5
            if label_y < 10:
                label_y = y2 + 5  # 如果上方空间不足，画在下方

            # 绘制标签背景（绿色）
            cv2.rectangle(
                annotated_image,
                (x1, label_y - 2),
                (x1 + text_width + 4, label_y + text_height + 2),
                (0, 255, 0),
                -1  # 填充
            )

            # 绘制标签文字（黑色）
            cv2.putText(
                annotated_image,
                label,
                (x1 + 2, label_y + text_height),
                font,
                font_scale,
                (0, 0, 0),
                font_thickness,
                cv2.LINE_AA  # 抗锯齿
            )

        return annotated_image

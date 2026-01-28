"""奶牛检测工具。

使用本地 YOLO 模型检测图像或视频中的奶牛。
"""
import json
import os
import cv2
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ultralytics import YOLO
from langchain_core.tools import tool


MODEL_DIR = Path("src/algorithms/cow_detection/detector/models")
MODEL_FILE = "yolov8n.pt"
RESULTS_DIR = Path("cow_detection_results")


def get_model_path() -> Path:
    """获取模型文件的绝对路径。

    Returns:
        模型文件的 Path 对象
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent.absolute()
    return project_root / MODEL_DIR / MODEL_FILE


def load_model() -> YOLO | None:
    """加载 YOLO 模型。

    Returns:
        加载的 YOLO 模型，失败返回 None
    """
    model_path = get_model_path()

    if not model_path.exists():
        return None

    return YOLO(str(model_path))


def detect_cows(image_path: str, model: YOLO) -> dict[str, Any]:
    """检测图片中的奶牛。

    Args:
        image_path: 图片文件路径
        model: YOLO 模型实例

    Returns:
        检测结果字典，包含奶牛数量、位置等信息
    """
    image = cv2.imread(image_path)
    if image is None:
        return {"success": False, "error": "无法读取图片文件"}

    height, width = image.shape[:2]
    results = model(image, verbose=False)

    cow_boxes = []
    for result in results:
        boxes = result.boxes
        if boxes:
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = model.names[class_id]

                if class_name.lower() == "cow":
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cow_boxes.append({
                        "class": "cow",
                        "confidence": confidence,
                        "bbox": [x1, y1, x2, y2],
                        "center": [(x1 + x2) / 2, (y1 + y2) / 2]
                    })

    RESULTS_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    result_image_name = f"cow_result_{timestamp}_{unique_id}.jpg"
    result_image_path = RESULTS_DIR / result_image_name

    result_image = image.copy()
    for cow in cow_boxes:
        x1, y1, x2, y2 = map(int, cow["bbox"])
        confidence = cow["confidence"]

        cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        label = f"Cow: {confidence:.2f}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        cv2.rectangle(
            result_image,
            (x1, y1 - label_size[1] - 4),
            (x1 + label_size[0], y1),
            (0, 255, 0),
            -1
        )
        cv2.putText(
            result_image,
            label,
            (x1, y1 - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            2
        )

    cv2.imwrite(str(result_image_path), result_image)

    return {
        "success": True,
        "cow_count": len(cow_boxes),
        "cow_boxes": cow_boxes,
        "image_size": {"width": width, "height": height},
        "result_image_path": str(result_image_path),
        "result_image_name": result_image_name
    }


def process_video(video_path: str, model: YOLO) -> dict[str, Any]:
    """处理视频文件中的奶牛检测。

    Args:
        video_path: 视频文件路径
        model: YOLO 模型实例

    Returns:
        检测结果字典，包含奶牛统计信息
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"success": False, "error": "无法打开视频文件"}

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frame_results = []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % 10 == 0:
            results = model(frame, verbose=False)
            cow_count = 0
            for result in results:
                boxes = result.boxes
                if boxes:
                    for box in boxes:
                        class_id = int(box.cls[0])
                        class_name = model.names[class_id]
                        if class_name.lower() == "cow":
                            cow_count += 1

            frame_results.append({
                "frame": frame_count,
                "time": frame_count / fps,
                "cow_count": cow_count
            })

        frame_count += 1

    cap.release()

    if frame_results:
        max_cows = max(r["cow_count"] for r in frame_results)
        avg_cows = sum(r["cow_count"] for r in frame_results) / len(frame_results)
    else:
        max_cows = 0
        avg_cows = 0

    return {
        "success": True,
        "video_info": {
            "duration": total_frames / fps,
            "fps": fps,
            "total_frames": total_frames
        },
        "detection_results": {
            "max_cows": max_cows,
            "avg_cows": avg_cows,
            "frame_results": frame_results
        }
    }


@tool
def cow_detection_tool(file_path: str) -> str:
    """检测图像或视频中的奶牛。

    该工具使用本地 YOLO 模型检测奶牛，支持：
    1. 图像检测：检测奶牛数量、位置，并保存带标注的结果图像
    2. 视频检测：统计视频中的奶牛数量变化

    Args:
        file_path: 本地文件路径，支持格式：
            - 图像：.jpg, .jpeg, .png, .bmp
            - 视频：.mp4, .avi, .mov

    Returns:
        JSON 格式的检测结果，包含：
        - success: 操作是否成功
        - cow_count: 奶牛数量（图像）
        - cow_boxes: 奶牛位置信息（图像）
        - result_image_path: 结果图像保存路径（图像）
        - max_cows: 最大奶牛数量（视频）
        - avg_cows: 平均奶牛数量（视频）
        - error: 错误信息（失败时）

    Examples:
        >>> cow_detection_tool("cows.jpg")
        '{"success": true, "cow_count": 3, ...}'

        >>> cow_detection_tool("farm.mp4")
        '{"success": true, "max_cows": 5, ...}'
    """
    if not file_path or not os.path.exists(file_path):
        return json.dumps(
            {"success": False, "error": f"文件路径不存在: {file_path}"},
            ensure_ascii=False
        )

    model = load_model()
    if model is None:
        return json.dumps(
            {"success": False, "error": f"模型文件不存在: {get_model_path()}"},
            ensure_ascii=False
        )

    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        if file_ext in {".jpg", ".jpeg", ".png", ".bmp"}:
            result = detect_cows(file_path, model)
        elif file_ext in {".mp4", ".avi", ".mov"}:
            result = process_video(file_path, model)
        else:
            return json.dumps(
                {"success": False, "error": f"不支持的文件格式: {file_ext}"},
                ensure_ascii=False
            )

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps(
            {"success": False, "error": f"检测处理失败: {str(e)}"},
            ensure_ascii=False
        )


__all__ = ["cow_detection_tool"]
cow_detection_tool.tags = ["detection", "cow"]

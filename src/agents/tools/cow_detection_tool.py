"""牛检测工具 - 简洁重构版本"""
import json
import os
import cv2
from ultralytics import YOLO
from langchain.tools import tool

def detect_cows(image_path: str, model) -> dict:
    """检测图片中的牛只"""
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
                
                if class_name.lower() == 'cow':
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cow_boxes.append({
                        'class': 'cow',
                        'confidence': confidence,
                        'bbox': [x1, y1, x2, y2],
                        'center': [(x1 + x2) / 2, (y1 + y2) / 2]
                    })
    
    return {
        "success": True,
        "cow_count": len(cow_boxes),
        "cow_boxes": cow_boxes,
        "image_size": {"width": width, "height": height}
    }


def process_video(video_path: str, model) -> dict:
    """处理视频文件中的牛只检测"""
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
                        if class_name.lower() == 'cow':
                            cow_count += 1
            
            frame_results.append({
                'frame': frame_count,
                'time': frame_count / fps,
                'cow_count': cow_count
            })
        
        frame_count += 1
    
    cap.release()
    
    max_cows = max([r['cow_count'] for r in frame_results]) if frame_results else 0
    avg_cows = sum([r['cow_count'] for r in frame_results]) / len(frame_results) if frame_results else 0
    
    return {
        "success": True,
        "video_info": {"duration": total_frames / fps, "fps": fps, "total_frames": total_frames},
        "detection_results": {"max_cows": max_cows, "avg_cows": avg_cows, "frame_results": frame_results}
    }


@tool
def cow_detection_tool(file_path: str) -> str:
    """检测图像或视频中的牛只。
    
    Args:
        file_path: 本地文件路径，支持.jpg, .jpeg, .png, .mp4, .avi, .mov格式
        
    Returns:
        JSON格式的检测结果
    """
    if not file_path or not os.path.exists(file_path):
        return json.dumps({"success": False, "error": f"文件路径不存在: {file_path}"}, ensure_ascii=False)
    
    try:
        # 使用标准化的模型路径
        model_path = os.path.join('src', 'algorithms', 'cow_detection', 'weights', 'yolov8n.pt')
        model = YOLO(model_path)
    except Exception as e:
        return json.dumps({"success": False, "error": f"模型加载失败: {e}"}, ensure_ascii=False)
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            result = detect_cows(file_path, model)
        elif file_ext in ['.mp4', '.avi', '.mov']:
            result = process_video(file_path, model)
        else:
            return json.dumps({"success": False, "error": f"不支持的文件格式: {file_ext}"}, ensure_ascii=False)
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"success": False, "error": f"检测处理失败: {str(e)}"}, ensure_ascii=False)


if __name__ == "__main__":
    # 测试工具
    test_image = "test.jpg"
    if os.path.exists(test_image):
        result = cow_detection_tool.invoke(test_image)
        print("检测结果:", result)
    else:
        print("测试图片不存在，请提供有效的图片路径")
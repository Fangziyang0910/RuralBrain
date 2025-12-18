import requests
import base64
import os
import uuid
from datetime import datetime
from pathlib import Path
from langchain_core.tools import tool
from typing import Dict, Any

API_URL = "http://127.0.0.1:8081/predict"
# 定义结果保存目录
RESULT_IMAGES_DIR = Path("rice_detection_results")

# 1. 新增辅助函数：保存检测结果图像到本地 (参考害虫检测工具)
def save_result_image(image_base64: str) -> str:
    """保存检测结果图像到本地。
    
    Args:
        image_base64: base64编码的结果图像
        
    Returns:
        保存的图像文件路径
    """
    # 确保结果目录存在
    RESULT_IMAGES_DIR.mkdir(exist_ok=True)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 生成唯一文件名，防止同一秒并发冲突
    filename = f"rice_detection_{timestamp}_{str(uuid.uuid4())[:8]}.jpg"
    filepath = RESULT_IMAGES_DIR / filename
    
    # 解码并保存图像
    try:
        image_data = base64.b64decode(image_base64)
        with open(filepath, "wb") as f:
            f.write(image_data)
        return str(filepath)
    except Exception as e:
        print(f"保存结果图片失败: {e}")
        return ""

# 2. 辅助函数：处理图片编码 (保持原样)
def encode_image_to_base64(image_path: str) -> str:
    """读取本地图片并转换为 Base64"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"文件不存在: {image_path}")
    
    # 这里可以加一些简单的格式校验，例如检查文件是否是图片格式
    if not image_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp')):
        raise ValueError(f"不支持的图片格式: {image_path}")
    
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

# 3. 辅助函数：格式化结果给 LLM 看 (微调)
def format_rice_result(api_response: Dict[str, Any]) -> str:
    """将后端复杂的 JSON 简化为 LLM 易读的自然语言"""
    if not api_response.get("success"):
        return f"识别服务报错: {api_response.get('message', '未知错误')}"
    
    detections = api_response.get("detections", [])
    if not detections:
        return "识别完成，但在图片中未检测到明显的大米颗粒。"
    
    # 拼接结果
    summary = []
    for item in detections:
        name = item.get("name", "未知品种")
        count = item.get("count", 0)
        summary.append(f"{name}({count}粒)")
    
    result_str = "识别成功。检测结果: " + "、".join(summary)
    
    return result_str

@tool
def rice_detection_tool(image_path: str, task_type: str = "品种分类") -> str:
    """
    调用大米识别服务。
    Args:
        image_path: 本地图片的绝对路径。
        task_type: 任务类型，默认为'品种分类'。
    Returns:
        识别结果的文字摘要。
    """
    try:
        # 1. 准备数据
        img_base64 = encode_image_to_base64(image_path)
        payload = {
            "image_base64": img_base64,
            "task_type": task_type,
            "session_id": str(uuid.uuid4())  # 生成一个唯一的 session_id
        }
        
        # 2. 调用 API
        resp = requests.post(API_URL, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
        resp.raise_for_status()
        
        api_response = resp.json()

        # 3. 保存结果图片 (新增逻辑)
        # 假设后端返回的字段名为 'result_image' (base64格式)，这通常是通用的约定
        if api_response.get("success") and api_response.get("result_image"):
            save_result_image(api_response["result_image"])
        
        # 4. 格式化并返回
        return format_rice_result(api_response)

    except Exception as e:
        return f"工具调用过程发生错误: {str(e)}"
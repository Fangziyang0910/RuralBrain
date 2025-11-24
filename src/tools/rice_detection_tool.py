import requests
import base64
import os
import uuid
from langchain_core.tools import tool
from typing import Dict, Any

API_URL = "http://127.0.0.1:8081/predict"

# 1. 辅助函数：处理图片编码
def encode_image_to_base64(image_path: str) -> str:
    """读取本地图片并转换为 Base64"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"文件不存在: {image_path}")
    
    # 这里可以加一些简单的格式校验，例如检查文件是否是图片格式
    if not image_path.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise ValueError(f"不支持的图片格式: {image_path}")
    
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

# 2. 辅助函数：格式化结果给 LLM 看
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
    
    # 注意：我们不再返回 result_image 的 base64 给 LLM
    # 如果后端生成了标记图，我们可以返回保存路径（如果后端支持返回路径的话）
    # 或者直接忽略图片返回，只告诉 LLM 结果文本。
    return result_str

@tool
def rice_recognition_tool(image_path: str, task_type: str = "品种分类") -> str:
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
        
        # 3. 格式化并返回
        # 这里直接返回字符串，LLM 读起来更轻松，且完全没有 Token 爆炸风险
        return format_rice_result(resp.json())

    except Exception as e:
        return f"工具调用过程发生错误: {str(e)}"
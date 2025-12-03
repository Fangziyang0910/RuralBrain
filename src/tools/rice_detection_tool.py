import requests
import base64
import os
import uuid
import time
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
            "session_id": str(uuid.uuid4())
        }
        
        # 2. 调用 API
        resp = requests.post(API_URL, json=payload, headers={'Content-Type': 'application/json'}, timeout=60)
        resp.raise_for_status()
        
        # 获取原始 JSON 结果
        result = resp.json()

        # --- [新增] 拦截并保存标注图片 (核心逻辑) ---
        # 师兄要求：Tools内部获取图片后不提供给LLM，用state存起来(此处暂存文件模拟)
        if result.get("success") and result.get("result_image"):
            try:
                # 提取 Base64 字符串
                img_b64 = result["result_image"]
                
                # 定义保存路径 (项目根目录/res/labeled_images/)
                # 这里模拟将图片存入"前端可访问的资源目录"
                save_dir = os.path.join("res", "labeled_images")
                os.makedirs(save_dir, exist_ok=True)
                
                # 生成唯一文件名
                filename = f"labeled_{int(time.time())}.jpg"
                file_path = os.path.join(save_dir, filename)
                
                # 解码并写入磁盘
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                
                print(f"✅ [Tool] 后端标注图片已拦截并保存至: {file_path}")
                
                # [关键步骤] 阉割数据：
                # 从字典中彻底删除 result_image 字段，确保巨大的 Base64 串
                # 绝对不会传递给 format_rice_result，也不会进入 LLM 的上下文。
                del result["result_image"]
                
            except Exception as e:
                print(f"⚠️ [Tool] 保存标注图片时发生错误 (不影响主流程): {e}")

        # 3. 格式化并返回 (此时 result 里已经没有图片数据了，只有纯文本统计)
        return format_rice_result(result)

    except Exception as e:
        return f"工具调用过程发生错误: {str(e)}"
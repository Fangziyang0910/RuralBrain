import requests
import base64
import os
from langchain_core.tools import tool
from typing import Optional

# 定义常量
API_URL = "http://127.0.0.1:8081/predict"

@tool
def rice_recognition_tool(task_type: str, image_path: Optional[str] = None, image_base64: Optional[str] = None) -> dict:
    """
    （网络版）大米识别工具。
    当你需要根据图片识别大米的品种或新旧时使用此工具。
    
    Args:
        task_type: 识别任务的类型，必须是 '品种分类' 或 '新旧识别' 中的一个。
        image_path: 本地图片的绝对路径（例如 /home/user/rice.jpg）。优先使用此参数。
        image_base64: 图片的Base64编码字符串。如果提供了路径，则不需要提供此项。
    """
    
    # --- 以下逻辑与之前的 _run 方法完全一致 ---
    try:
        final_base64 = image_base64

        # 1. 处理输入：如果 Agent 传来了路径，工具负责转成 Base64
        if image_path and not final_base64:
            if os.path.exists(image_path):
                try:
                    with open(image_path, "rb") as f:
                        final_base64 = base64.b64encode(f.read()).decode('utf-8')
                except Exception as e:
                    return {"success": False, "message": f"读取本地文件失败: {str(e)}"}
            else:
                return {"success": False, "message": f"文件不存在: {image_path}"}
        
        # 校验
        if not final_base64:
            return {"success": False, "message": "参数错误：必须提供图片路径(image_path)或Base64编码(image_base64)"}

        # 2. 调用后端 API
        payload = {
            "image_base64": final_base64,
            "task_type": task_type
        }
        headers = {'Content-Type': 'application/json'}

        response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        full_result = response.json()

        # 3. Token 瘦身 (核心修复)
        safe_result = full_result.copy()
        if "result_image" in safe_result:
            safe_result["result_image"] = "<image_base64_hidden_to_save_tokens>"
        
        return safe_result

    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"调用API时发生网络错误: {e}"}
    except Exception as e:
        return {"success": False, "message": f"处理API响应时发生未知错误: {e}"}
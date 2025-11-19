import requests
import base64
import os
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional

# --- 修改点 1: 输入模型要兼容 Path 和 Base64 ---
class RiceRecognitionInput(BaseModel):
    """大米识别工具的输入模型"""
    # 允许 LLM 传入路径 (这是给 Agent 用的主要参数)
    image_path: Optional[str] = Field(
        default=None, 
        description="本地图片的绝对路径（例如 /home/user/rice.jpg）。优先使用此参数。"
    )
    # 保留 Base64 接口 (为了灵活性)
    image_base64: Optional[str] = Field(
        default=None, 
        description="图片的Base64编码字符串。如果提供了路径，则不需要提供此项。"
    )
    task_type: str = Field(description="识别任务的类型，必须是 '品种分类' 或 '新旧识别' 中的一个。")


class RiceRecognitionApiTool(BaseTool):
    """
    一个通过调用API来识别大米种类或新旧的工具。
    它将本地图片文件上传到远程服务器进行分析，
    并返回一个总结性的文本和一张标注了结果的图片路径。
    """
    name: str = "rice_recognizer_api"
    # --- 修改点 2: 描述要明确告诉 LLM 可以传路径 ---
    description: str = (
        "（网络版）当你需要根据图片识别大米的品种或新旧时使用此工具。"
        "你可以提供图片的本地文件路径 (image_path)，工具会自动处理上传。"
        "你需要提供任务类型（'品种分类' 或 '新旧识别'）。"
    )
    args_schema: Type[BaseModel] = RiceRecognitionInput

    # 定义API服务器的地址
    api_url: str = "http://127.0.0.1:8081/predict"

     # --- 修改点：_run 方法内部 ---
    def _run(self, task_type: str, image_path: str = None, image_base64: str = None) -> dict:
        """同步执行工具，并返回结构化的JSON（字典）。"""
        try:
            final_base64 = image_base64

            # --- 1. 处理输入：如果 Agent 传来了路径，工具负责转成 Base64 ---
            if image_path and not final_base64:
                if os.path.exists(image_path):
                    try:
                        with open(image_path, "rb") as f:
                            # 读取并转码
                            final_base64 = base64.b64encode(f.read()).decode('utf-8')
                    except Exception as e:
                        return {"success": False, "message": f"读取本地文件失败: {str(e)}"}
                else:
                    return {"success": False, "message": f"文件不存在: {image_path}"}
            
            # 校验：既没有路径也没有 Base64
            if not final_base64:
                return {"success": False, "message": "参数错误：必须提供图片路径(image_path)或Base64编码(image_base64)"}

            # --- 2. 调用后端 API ---
            payload = {
                "image_base64": final_base64,
                "task_type": task_type
            }
            headers = {'Content-Type': 'application/json'}

            # 发送 POST 请求
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=60)

            # 检查响应状态码
            response.raise_for_status()

            # 获取原始结果 (包含巨大的 Base64 图片数据)
            full_result = response.json()

            # --- 3. 【关键修复】Token 瘦身 ---
            # 我们不能把包含几十万字符的 Base64 图片直接扔给 LLM，这会撑爆 Context Window (400 Bad Request)
            # 所以我们需要创建一个“给 LLM 看的副本”，把图片数据隐藏掉
            
            safe_result = full_result.copy()
            
            if "result_image" in safe_result:
                # 替换为占位符。LLM 不需要看图片数据也能回答问题（它只需要看 detections 里的统计数据）。
                safe_result["result_image"] = "<image_base64_hidden_to_save_tokens>"
            
            # 返回处理后的轻量级 JSON 给 Agent
            return safe_result

        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"调用API时发生网络错误: {e}"}
        except Exception as e:
            return {"success": False, "message": f"处理API响应时发生未知错误: {e}"}

    async def _arun(self, *args, **kwargs):
        # 对于IO密集型任务，异步实现会更高效，但这里为了简单，直接调用同步版本
        return self._run(*args, **kwargs)
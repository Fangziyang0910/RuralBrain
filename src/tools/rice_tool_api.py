import requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import os


class RiceRecognitionInput(BaseModel):
    """大米识别工具的输入模型"""
    image_base64: str = Field(description="必须是经过 base64 编码的图片字符串。")
    task_type: str = Field(description="识别任务的类型，必须是 '品种分类' 或 '新旧识别' 中的一个。")


class RiceRecognitionApiTool(BaseTool):
    """
    一个通过调用API来识别大米种类或新旧的工具。
    它将本地图片文件上传到远程服务器进行分析，
    并返回一个总结性的文本和一张标注了结果的图片路径。
    """
    name: str = "rice_recognizer_api"
    description: str = (
        "（网络版）当你需要根据图片识别大米的品种或新旧时使用此工具。"
        "它通过网络API工作，适用于需要将计算任务卸载到服务器的场景。"
        "你需要提供图片的本地文件路径和任务类型（'品种分类' 或 '新旧识别'）。"
    )
    args_schema: Type[BaseModel] = RiceRecognitionInput

    # 定义API服务器的地址
    api_url: str = "http://127.0.0.1:8081/predict"

    def _run(self, image_base64: str, task_type: str) -> dict:
        """同步执行工具，并返回结构化的JSON（字典）。"""
        try:
            # 准备 JSON 载荷
            payload = {
                "image_base64": image_base64,
                "task_type": task_type  # 假设你的API也同步修改为接收task_type
            }
            headers = {'Content-Type': 'application/json'}

            # 发送 POST 请求
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=60)

            # 检查响应状态码
            response.raise_for_status()

            # 直接返回API响应的JSON内容（它本身就是一个字典）
            return response.json()

        except requests.exceptions.RequestException as e:
            # 返回符合规范的结构化错误信息
            return {"success": False, "message": f"调用API时发生网络错误: {e}"}
        except Exception as e:
            # 返回符合规范的结构化错误信息
            return {"success": False, "message": f"处理API响应时发生未知错误: {e}"}

    async def _arun(self, *args, **kwargs):
        # 对于IO密集型任务，异步实现会更高效，但这里为了简单，直接调用同步版本
        return self._run(*args, **kwargs)
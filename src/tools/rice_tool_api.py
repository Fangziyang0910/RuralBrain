import requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import os


class RiceRecognitionInput(BaseModel):
    """大米识别工具的输入模型"""
    image_path: str = Field(description="必须是本地图片文件的绝对路径。")
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

    def _run(self, image_path: str, task_type: str) -> str:
        """同步执行工具。"""
        if not os.path.exists(image_path):
            return f"错误：文件未找到 - {image_path}"

        try:
            # 准备要上传的文件和表单数据
            with open(image_path, 'rb') as f:
                files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
                data = {'task_type': task_type}

                # 发送 POST 请求
                response = requests.post(self.api_url, files=files, data=data, timeout=60)  # 设置60秒超时

            # 检查响应状态码
            response.raise_for_status()  # 如果状态码不是 2xx，则会引发HTTPError异常

            # 解析JSON响应
            result = response.json()

            # 格式化结果为自然语言字符串
            if result.get("success"):
                summary_lines = [f"图像 {os.path.basename(image_path)} 的大米 {result['task_type']} 结果分析:"]
                for item in result['analysis']:
                    summary_lines.append(f"- {item['label']}: {item['count']} 个, 占比 {item['percentage']}%")
                summary_lines.append(f"总计: {result['total_count']} 个。")
                summary_text = "\n".join(summary_lines)

                return (
                    f"通过API识别成功。\n"
                    f"分析摘要:\n{summary_text}\n"
                    f"已标注的结果图片保存在服务器的路径: {result['annotated_image_path']}"
                )
            else:
                return f"API返回错误: {result.get('error', '未知错误')}"

        except requests.exceptions.RequestException as e:
            return f"调用API时发生网络错误: {e}. 请确保API服务 (app.py) 正在运行中。"
        except Exception as e:
            return f"处理API响应时发生未知错误: {e}"

    async def _arun(self, *args, **kwargs):
        # 对于IO密集型任务，异步实现会更高效，但这里为了简单，直接调用同步版本
        return self._run(*args, **kwargs)
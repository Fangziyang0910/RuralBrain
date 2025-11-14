from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

# 导入我们刚刚创建的核心逻辑函数
from .rice_recognizer import recognize_rice_from_image

class RiceRecognitionInput(BaseModel):
    """大米识别工具的输入模型"""
    image_path: str = Field(description="必须是本地图片文件的绝对路径。")
    task_type: str = Field(description="识别任务的类型，必须是 '品种分类' 或 '新旧识别' 中的一个。")

class RiceRecognitionTool(BaseTool):
    """
    一个用于识别大米种类或新旧程度的工具。
    它接收一个图片文件的本地路径，利用YOLO模型进行分析，
    并返回一个总结性的文本和一张标注了结果的图片路径。
    """
    name: str = "rice_recognizer"
    description: str = (
        "当你需要根据图片识别大米的具体品种（如糯米、丝苗米等）或新旧程度时，使用此工具。"
        "你需要提供图片的本地文件路径和任务类型（'品种分类' 或 '新旧识别'）。"
    )
    args_schema: Type[BaseModel] = RiceRecognitionInput

    def _run(self, image_path: str, task_type: str) -> str:
        """同步执行工具。"""
        # 调用核心逻辑函数
        result = recognize_rice_from_image(image_path=image_path, task_type=task_type)

        # 根据返回结果，格式化为最终的字符串输出
        if "error" in result:
            return f"识别失败: {result['error']}"
        else:
            return (
                f"识别成功。\n"
                f"分析摘要:\n{result['summary']}\n"
                f"已标注的结果图片保存在: {result['annotated_image_path']}"
            )

    async def _arun(self, image_path: str, task_type: str) -> str:
        """异步执行（当前示例为简单包装，未来可优化为真正的异步IO）。"""
        # 在这个场景下，模型预测是CPU密集型，伪异步即可
        return self._run(image_path, task_type)
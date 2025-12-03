import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# 注意这里我们导入的是新的 API Tool
from src.tools.rice_tool_api import RiceRecognitionApiTool

if __name__ == "__main__":
    print("--- 正在测试大米识别API工具 ---")

    rice_tool = RiceRecognitionApiTool()

    image_path = os.path.abspath("test_data/test_rice.jpg")
    task_type = "品种分类"

    print(f"输入图片路径: {image_path}")
    print(f"任务类型: {task_type}")

    if not os.path.exists(image_path):
        print(f"\n错误：测试图片不存在！")
    else:
        print("\n--- 调用API工具 ---")
        result_str = rice_tool.run(
            {"image_path": image_path, "task_type": task_type}
        )
        print("\n--- 工具返回结果 ---")
        print(result_str)
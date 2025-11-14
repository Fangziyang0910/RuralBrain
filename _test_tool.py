import os
from src.tools.rice_tool import RiceRecognitionTool

# 确保我们能找到 src 目录
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

if __name__ == "__main__":
    print("--- 正在测试大米识别工具 ---")

    # 1. 实例化工具
    rice_tool = RiceRecognitionTool()

    # 2. 准备输入参数
    # 注意：这里需要使用绝对路径
    image_path = os.path.abspath("test_data/test_rice.jpg")
    task_type = "品种分类"  # 你可以把它改成 "新旧识别" 来测试另一种模式

    print(f"输入图片路径: {image_path}")
    print(f"任务类型: {task_type}")

    # 检查图片是否存在
    if not os.path.exists(image_path):
        print(f"\n错误：测试图片不存在！请确保在 'test_data/test_rice.jpg' 路径下放置了测试图片。")
    else:
        # 3. 运行工具
        print("\n--- 调用工具 ---")
        result_str = rice_tool.run(tool_input={"image_path": image_path, "task_type": task_type})

        # 4. 打印结果
        print("\n--- 工具返回结果 ---")
        print(result_str)
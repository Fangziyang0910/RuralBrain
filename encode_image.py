# 文件名: encode_image.py
import base64
import json
import os

# --- 配置 ---
# 你的测试图片路径
image_path = "/home/szh/projects/RuralBrain/test_data/test_rice.jpg"
# 我们要保存的测试数据文件名
output_json_path = "test_input.json"

def create_test_data():
    """读取图片，将其编码为Base64，并保存到JSON文件中。"""
    if not os.path.exists(image_path):
        print(f"错误：找不到图片文件 '{image_path}'")
        return

    try:
        # 读取图片二进制数据
        with open(image_path, "rb") as image_file:
            # 进行 Base64 编码
            base64_string = base64.b64encode(image_file.read()).decode('utf-8')

        # 构建符合API输入规范的JSON对象
        payload = {
            "image_base64": base64_string
        }

        # 将这个对象写入文件
        with open(output_json_path, "w") as json_file:
            json.dump(payload, json_file, indent=2)

        print(f"✅ 测试数据准备成功！")
        print(f"图片 '{image_path}' 的Base64编码已保存到 '{output_json_path}' 文件中。")

    except Exception as e:
        print(f"创建测试数据时发生错误: {e}")

if __name__ == "__main__":
    create_test_data()
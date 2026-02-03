"""
疾病预测工具测试脚本

测试 disease_prediction_tool 的功能
"""
import sys
import os
from pathlib import Path

# 设置控制台编码为 UTF-8（解决 Windows 中文乱码问题）
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("疾病预测工具测试")
print("=" * 60)

# 检查环境变量
api_key_set = bool(os.getenv("DEEPSEEK_API_KEY"))
print(f"DEEPSEEK_API_KEY: {'已设置' if api_key_set else '未设置'}")
print(f"MODEL_PROVIDER: {os.getenv('MODEL_PROVIDER', '未设置')}")
print()

from src.agents.tools.disease_prediction_tool import disease_prediction_tool


def test_case(name, params):
    """运行单个测试用例"""
    print(f"\n{'=' * 60}")
    print(f"测试用例: {name}")
    print(f"{'=' * 60}")
    print(f"参数: {params}")
    print(f"\n结果:")

    try:
        result = disease_prediction_tool.invoke(params)
        print(result)
        return True
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


# 定义测试用例
test_cases = [
    ("牛发热咳嗽", {
        "animal_type": "牛",
        "symptoms": "发热、咳嗽、精神萎靡",
        "temperature": 39.8
    }),
    ("猪拉稀", {
        "animal_type": "猪",
        "symptoms": "拉稀、不食",
        "temperature": 39.2
    }),
    ("鸡精神萎靡", {
        "animal_type": "鸡",
        "symptoms": "精神萎靡、羽毛蓬松"
    }),
    ("羊体温高", {
        "animal_type": "羊",
        "symptoms": "咳嗽、不食",
        "temperature": 40.0
    }),
]

# 运行测试
passed = 0
total = len(test_cases)

for name, params in test_cases:
    if test_case(name, params):
        passed += 1

print(f"\n{'=' * 60}")
print(f"测试完成: {passed}/{total} 通过")
print(f"{'=' * 60}")

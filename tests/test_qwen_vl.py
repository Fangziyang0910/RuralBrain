"""
Qwen3.5-Plus 多模态模型测试脚本

测试阿里云百炼 Qwen3.5-Plus 模型的多模态能力。
Qwen3.5-Plus 原生支持多模态，无需单独的视觉模型。

使用方法:
    uv run python tests/test_qwen_vl.py

环境要求:
    - 设置 QWEN_API_KEY 环境变量
"""
import os
import sys
from pathlib import Path

# 设置控制台编码（Windows 兼容）
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from src.utils import ModelManager, MultimodalHelper


def test_model_manager_qwen():
    """测试 ModelManager 获取 Qwen 模型"""
    print("=" * 50)
    print("测试 1: ModelManager 获取 Qwen 模型")
    print("=" * 50)

    # 检查 API Key
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key or api_key == "your_qwen_api_key_here":
        print("❌ 错误: 请在 .env 文件中设置 QWEN_API_KEY")
        return False

    try:
        # Qwen3.5-Plus 原生支持多模态
        manager = ModelManager(provider="qwen")
        model = manager.get_chat_model()
        print(f"✓ 成功创建 Qwen 模型: {model.model_name}")
        print(f"  默认模型: {manager.config['default_model']}")

        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_multimodal_helper():
    """测试 MultimodalHelper 构建消息"""
    print("\n" + "=" * 50)
    print("测试 2: MultimodalHelper 构建消息")
    print("=" * 50)

    # 测试构建图片内容块
    try:
        # 模拟 base64 数据
        fake_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        content = MultimodalHelper.build_image_content(
            base64_data=fake_base64,
            mime_type="image/png"
        )
        print(f"✓ 构建图片内容块成功: type={content['type']}")

        # 测试构建消息
        message = MultimodalHelper.build_image_message(
            text="描述这张图片",
            base64_data=fake_base64,
            mime_type="image/png"
        )
        print(f"✓ 构建单图消息成功: content 长度={len(message.content)}")

        # 测试多图消息
        multi_message = MultimodalHelper.build_multi_image_message(
            text="比较这两张图片",
            image_urls=["https://example.com/img1.jpg", "https://example.com/img2.jpg"]
        )
        print(f"✓ 构建多图消息成功: content 长度={len(multi_message.content)}")

        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False


def test_multimodal_model_call():
    """测试多模态模型调用（需要真实图片）"""
    print("\n" + "=" * 50)
    print("测试 3: 多模态模型调用（需要网络）")
    print("=" * 50)

    # 检查 API Key
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key or api_key == "your_qwen_api_key_here":
        print("❌ 跳过: 请在 .env 文件中设置 QWEN_API_KEY")
        return None

    try:
        manager = ModelManager(provider="qwen")
        model = manager.get_chat_model()

        # 使用网络图片测试
        test_image_url = "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"

        message = MultimodalHelper.build_image_message(
            text="请简单描述这张图片的内容",
            image_url=test_image_url
        )

        print("正在调用 Qwen3.5-Plus 模型...")
        response = model.invoke([message])

        print(f"✓ 模型调用成功!")
        print(f"响应内容: {response.content[:200]}...")

        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Qwen3.5-Plus 多模态模型集成测试")
    print("=" * 60 + "\n")

    results = []

    # 测试 1: ModelManager
    results.append(("ModelManager Qwen 模型", test_model_manager_qwen()))

    # 测试 2: MultimodalHelper
    results.append(("MultimodalHelper", test_multimodal_helper()))

    # 测试 3: 实际模型调用
    results.append(("多模态模型调用", test_multimodal_model_call()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, result in results:
        status = "✓ 通过" if result else ("⊘ 跳过" if result is None else "✗ 失败")
        print(f"  {name}: {status}")

    # 返回是否全部通过
    all_passed = all(r for r in results if r is not None)
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
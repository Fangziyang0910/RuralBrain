"""
测试模型管理器功能
"""
import os
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

from src.utils import ModelManager
from src.config import DEFAULT_PROVIDER, MODEL_CONFIGS

def test_model_manager():
    print("=" * 60)
    print("测试模型管理器")
    print("=" * 60)
    
    # 测试1: 显示当前配置
    print(f"\n1. 当前默认供应商: {DEFAULT_PROVIDER}")
    print(f"   支持的供应商: {list(MODEL_CONFIGS.keys())}")
    
    # 测试2: 测试 DeepSeek
    print("\n2. 测试创建 DeepSeek 模型...")
    if os.getenv("DEEPSEEK_API_KEY"):
        try:
            manager_ds = ModelManager(provider="deepseek")
            model_ds = manager_ds.get_chat_model()
            print(f"   ✓ DeepSeek 模型创建成功")
            print(f"   模型类型: {type(model_ds).__name__}")
            # ChatDeepSeek 使用 model_name 而不是 model
            model_name = getattr(model_ds, 'model_name', getattr(model_ds, 'model', 'N/A'))
            print(f"   模型名称: {model_name}")
        except Exception as e:
            print(f"   ✗ DeepSeek 模型创建失败: {e}")
    else:
        print("   ⊗ 跳过 (未设置 DEEPSEEK_API_KEY)")
    
    # 测试3: 测试 GLM
    print("\n3. 测试创建 GLM 模型...")
    if os.getenv("ZHIPUAI_API_KEY"):
        try:
            manager_glm = ModelManager(provider="glm")
            model_glm = manager_glm.get_chat_model()
            print(f"   ✓ GLM 模型创建成功")
            print(f"   模型类型: {type(model_glm).__name__}")
            # ChatOpenAI 使用 model_name 属性
            model_name = getattr(model_glm, 'model_name', 'N/A')
            print(f"   模型名称: {model_name}")
            base_url = getattr(model_glm, 'openai_api_base', getattr(model_glm, 'base_url', 'N/A'))
            print(f"   Base URL: {base_url}")
        except Exception as e:
            print(f"   ✗ GLM 模型创建失败: {e}")
    else:
        print("   ⊗ 跳过 (未设置 ZHIPUAI_API_KEY)")
    
    # 测试4: 测试从环境变量加载
    print("\n4. 测试从环境变量加载模型...")
    try:
        manager_env = ModelManager.from_env()
        model_env = manager_env.get_chat_model()
        print(f"   ✓ 环境变量模型创建成功")
        print(f"   供应商: {manager_env.provider}")
        print(f"   模型类型: {type(model_env).__name__}")
    except Exception as e:
        print(f"   ✗ 环境变量模型创建失败: {e}")
    
    # 测试5: 测试自定义参数
    print("\n5. 测试自定义参数...")
    if os.getenv("DEEPSEEK_API_KEY"):
        try:
            manager_custom = ModelManager(provider="deepseek")
            model_custom = manager_custom.get_chat_model(
                temperature=0.7,
                model="deepseek-chat"
            )
            print(f"   ✓ 自定义参数模型创建成功")
            print(f"   温度参数: {model_custom.temperature}")
            model_name = getattr(model_custom, 'model_name', getattr(model_custom, 'model', 'N/A'))
            print(f"   模型名称: {model_name}")
        except Exception as e:
            print(f"   ✗ 自定义参数模型创建失败: {e}")
    else:
        print("   ⊗ 跳过 (未设置 DEEPSEEK_API_KEY)")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    test_model_manager()

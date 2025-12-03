"""
误判误检测试脚本 - 测试错误检测需求下的系统响应
测试场景:给出错误的检测需求,验证底层算法工具是否会误判
例如:上传害虫图片但要求检测大米,看大米检测工具是否会误报结果
"""
from dotenv import load_dotenv
import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

print("正在加载 AI 模型和工具...")
sys.stdout.flush()

from src.agents.image_detection_agent import agent as image_detection_agent
from langchain_core.messages import HumanMessage, AIMessageChunk

print("✓ 系统加载完成！\n")


# 定义测试用例 - 每个用例包含图片路径和错误的检测需求
# 格式: (图片路径, 实际类型, 错误需求)
TEST_CASES = [
    {
        "image": "tests/resources/mixed/1.jpg",
        "actual_type": "害虫",
        "wrong_request": "大米",
        "description": "上传害虫图片,要求检测大米"
    },
    {
        "image": "tests/resources/mixed/2.jpg",
        "actual_type": "害虫",
        "wrong_request": "牛只",
        "description": "上传害虫图片,要求检测牛只"
    },
    {
        "image": "tests/resources/mixed/3.jpg",
        "actual_type": "大米",
        "wrong_request": "害虫",
        "description": "上传大米图片,要求检测害虫"
    },
    {
        "image": "tests/resources/mixed/4.jpg",
        "actual_type": "大米",
        "wrong_request": "牛只",
        "description": "上传大米图片,要求检测牛只"
    },
    {
        "image": "tests/resources/mixed/5.jpg",
        "actual_type": "牛只",
        "wrong_request": "害虫",
        "description": "上传牛只图片,要求检测害虫"
    },
    {
        "image": "tests/resources/mixed/6.jpg",
        "actual_type": "牛只",
        "wrong_request": "大米",
        "description": "上传牛只图片,要求检测大米"
    },
]


def run_test():
    """运行误判误检测试"""
    config = {"configurable": {"thread_id": "misdetection_test_001"}}
    
    print("=" * 80)
    print("开始误判误检测试")
    print("测试目标: 验证系统在收到错误检测需求时是否会误判")
    print("=" * 80)
    print()
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{'=' * 80}")
        print(f"测试 {i}/{len(TEST_CASES)}")
        print(f"{'=' * 80}")
        print(f"📝 测试说明: {test_case['description']}")
        print(f"📷 图片路径: {test_case['image']}")
        print(f"✅ 实际类型: {test_case['actual_type']}")
        print(f"❌ 错误需求: {test_case['wrong_request']}")
        print(f"{'-' * 80}")
        
        # 构造完整的用户输入
        user_input = f"请帮我检测这张图片中的{test_case['wrong_request']}：{test_case['image']}"
        print(f"\n用户> {user_input}")
        print(f"助手> ", end="", flush=True)
        
        try:
            # 发送完整的检测请求
            for chunk, metadata in image_detection_agent.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config,
                stream_mode="messages",
            ):
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    print(chunk.content, end="", flush=True)
            
            print("\n")
            
            # 每次测试后稍作停顿
            if i < len(TEST_CASES):
                print(f"\n⏱️  等待 2 秒后继续下一个测试...\n")
                time.sleep(2)
                
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}\n")
            continue
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
    print("\n📊 测试总结:")
    print("   - 请检查上述输出,验证系统是否正确拒绝了错误的检测需求")
    print("   - 理想情况:系统应识别出图片类型与用户需求不匹配")
    print("   - 误判情况:系统错误地执行了不匹配的检测任务")


def main():
    """主函数"""
    try:
        run_test()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

"""
自动测试脚本 - 农业图像识别 Agent 测试
依次测试多个输入场景，验证 agent 的响应能力
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


# 定义测试用例
TEST_CASES = [
    "你好",
    "tests/resources/pests/1.jpg",
    "这种害虫对农作物有什么危害？",
    "tests/resources/rice/1.jpg",
    "这两种大米有什么区别？",
    "tests/resources/cows/1.jpg",
    "养殖这个规模的牛群需要注意什么？",
    "tests/resources/pests/3.jpg tests/resources/rice/2.jpg tests/resources/cows/3.jpg",
    "什么是生物防治？",
    "大米怎么煮才好吃？",
    "养牛需要注意什么？",
]


def run_test():
    """运行自动测试"""
    config = {"configurable": {"thread_id": "auto_test_001"}}
    
    print("=" * 80)
    print("开始自动测试")
    print("=" * 80)
    print()
    
    for i, user_input in enumerate(TEST_CASES, 1):
        print(f"\n{'=' * 80}")
        print(f"测试 {i}/{len(TEST_CASES)}")
        print(f"{'=' * 80}")
        print(f"用户> {user_input}")
        print(f"\n助手> ", end="", flush=True)
        
        try:
            # 调用 agent 并流式输出
            for chunk, metadata in image_detection_agent.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config,
                stream_mode="messages",
            ):
                # 只输出 AI 消息内容
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    print(chunk.content, end="", flush=True)
            
            print("\n")
            
            # 每次测试后稍作停顿，避免请求过快
            if i < len(TEST_CASES):
                time.sleep(1)
                
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}\n")
            continue
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


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

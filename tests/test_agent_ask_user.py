"""
主动询问测试脚本 - 测试 Agent 在无法判断图片类型时是否会主动询问用户
测试场景: 给出没有明显类型信息的图片路径,验证 agent 是否会询问图片类型
例如: 输入 tests/resources/mixed/5.jpg,期望 agent 询问这是什么类型的图片
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


# 定义测试用例 - 每个用例包含图片路径和后续的用户回答
TEST_CASES = [
    {
        "image_path": "tests/resources/mixed/5.jpg",
        "user_answer": "牛只",
        "description": "输入模糊路径,期望询问后用户回答牛只"
    },
    {
        "image_path": "tests/resources/mixed/3.jpg",
        "user_answer": "大米",
        "description": "输入模糊路径,期望询问后用户回答大米"
    },
    {
        "image_path": "tests/resources/mixed/1.jpg",
        "user_answer": "害虫",
        "description": "输入模糊路径,期望询问后用户回答害虫"
    },
]


def run_test():
    """运行主动询问测试"""
    config = {"configurable": {"thread_id": "ask_user_test_001"}}
    
    print("=" * 80)
    print("开始主动询问测试")
    print("测试目标: 验证 Agent 在无法判断图片类型时是否会主动询问用户")
    print("=" * 80)
    print()
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{'=' * 80}")
        print(f"测试 {i}/{len(TEST_CASES)}")
        print(f"{'=' * 80}")
        print(f"📝 测试说明: {test_case['description']}")
        print(f"📷 图片路径: {test_case['image_path']}")
        print(f"💬 预期用户回答: {test_case['user_answer']}")
        print(f"{'-' * 80}")
        
        # 第一步: 发送图片路径
        first_input = test_case['image_path']
        print(f"\n用户> {first_input}")
        print(f"助手> ", end="", flush=True)
        
        agent_response = ""
        try:
            # 发送图片路径
            for chunk, metadata in image_detection_agent.stream(
                {"messages": [HumanMessage(content=first_input)]},
                config,
                stream_mode="messages",
            ):
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    print(chunk.content, end="", flush=True)
                    agent_response += chunk.content
            
            print("\n")
            
            # 等待一下,模拟真实交互
            time.sleep(1)
            
            # 第二步: 发送用户回答
            second_input = test_case['user_answer']
            print(f"用户> {second_input}")
            print(f"助手> ", end="", flush=True)
            
            # 继续对话
            for chunk, metadata in image_detection_agent.stream(
                {"messages": [HumanMessage(content=second_input)]},
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
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
    print("\n📊 测试总结:")
    print("   - 请检查上述输出,验证 agent 是否在第一次输入时主动询问了图片类型")
    print("   - 理想情况: agent 识别出无法从路径判断类型,主动询问用户")
    print("   - 然后根据用户的回答调用相应的检测工具")


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

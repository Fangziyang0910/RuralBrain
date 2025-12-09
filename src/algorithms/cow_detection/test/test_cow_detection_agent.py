"""
测试脚本 - 牛识别 Agent 对话功能测试
重点测试 cow_detection_agent 的图片识别后追问功能以及多图片连续对话能力
"""
from dotenv import load_dotenv
import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

print("正在加载牛识别 Agent...")
sys.stdout.flush()

from src.agents.cow_detection_agent import agent as cow_agent
from langchain_core.messages import HumanMessage, AIMessageChunk

print("✓ 系统加载完成！\n")


def test_image_follow_up_questions():
    """测试图片识别后的追问功能"""
    config = {"configurable": {"thread_id": "cow_follow_up_test_001"}}
    
    print("=" * 80)
    print("测试图片识别后的追问功能")
    print("=" * 80)
    
    # 第一张图片及其追问
    image_path_1 = str(project_root / "tests" / "resources" / "cows" / "1.jpg")
    follow_up_questions_1 = [
        "这些牛是什么品种？",
        "养殖这种牛有什么经济价值？",
        "这种牛适合什么规模的养殖？",
        "养殖这些牛需要注意什么？"
    ]
    
    print(f"\n用户> {image_path_1}")
    print(f"\n助手> ", end="", flush=True)
    
    try:
        # 发送第一张图片
        response_content = ""
        for chunk, metadata in cow_agent.stream(
            {"messages": [HumanMessage(content=image_path_1)]},
            config,
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                print(chunk.content, end="", flush=True)
                response_content += chunk.content
        
        print("\n")
        
        # 对第一张图片进行追问
        for i, question in enumerate(follow_up_questions_1, 1):
            print(f"\n用户> {question}")
            print(f"\n助手> ", end="", flush=True)
            
            response_content = ""
            for chunk, metadata in cow_agent.stream(
                {"messages": [HumanMessage(content=question)]},
                config,
                stream_mode="messages",
            ):
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    print(chunk.content, end="", flush=True)
                    response_content += chunk.content
            
            print("\n")
            time.sleep(1)
            
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}\n")
        import traceback
        traceback.print_exc()


def test_multi_image_conversation():
    """测试多图片连续对话能力"""
    config = {"configurable": {"thread_id": "cow_multi_image_test_001"}}
    
    print("\n" + "=" * 80)
    print("测试多图片连续对话能力")
    print("=" * 80)
    
    # 多张图片及其相关问题
    test_images = [
        {
            "path": str(project_root / "tests" / "resources" / "cows" / "1.jpg"),
            "questions": [
                "这些牛有什么特点？",
                "养殖这种牛有什么建议？"
            ]
        },
        {
            "path": str(project_root / "tests" / "resources" / "cows" / "5.jpg"),
            "questions": [
                "和之前的牛相比，这些牛有什么不同？",
                "这两种牛哪种更适合小规模养殖？"
            ]
        },
        {
            "path": str(project_root / "tests" / "resources" / "cows" / "10.jpg"),
            "questions": [
                "这批牛的数量看起来更多，它们适合什么规模的养殖场？",
                "综合来看，哪种牛的投资回报率更高？"
            ]
        }
    ]
    
    for i, image_test in enumerate(test_images, 1):
        print(f"\n{'=' * 40} 图片 {i} {'=' * 40}")
        
        # 发送图片
        print(f"\n用户> {image_test['path']}")
        print(f"\n助手> ", end="", flush=True)
        
        try:
            response_content = ""
            for chunk, metadata in cow_agent.stream(
                {"messages": [HumanMessage(content=image_test['path'])]},
                config,
                stream_mode="messages",
            ):
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    print(chunk.content, end="", flush=True)
                    response_content += chunk.content
            
            print("\n")
            
            # 对当前图片进行追问
            for j, question in enumerate(image_test['questions'], 1):
                print(f"\n用户> {question}")
                print(f"\n助手> ", end="", flush=True)
                
                response_content = ""
                for chunk, metadata in cow_agent.stream(
                    {"messages": [HumanMessage(content=question)]},
                    config,
                    stream_mode="messages",
                ):
                    if isinstance(chunk, AIMessageChunk) and chunk.content:
                        print(chunk.content, end="", flush=True)
                        response_content += chunk.content
                
                print("\n")
                time.sleep(1)
                
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}\n")
            import traceback
            traceback.print_exc()
        
        # 图片间稍作停顿
        if i < len(test_images):
            time.sleep(2)


def test_complex_conversation_flow():
    """测试复杂对话流程：混合图片、问题和追问"""
    config = {"configurable": {"thread_id": "cow_complex_test_001"}}
    
    print("\n" + "=" * 80)
    print("测试复杂对话流程")
    print("=" * 80)
    
    # 复杂对话流程
    conversation_flow = [
        "你好，我想了解养牛的相关知识",
        str(project_root / "tests" / "resources" / "cows" / "2.jpg"),
        "这些牛是什么品种？",
        "养殖这种牛有什么特殊要求吗？",
        str(project_root / "tests" / "resources" / "cows" / "11.jpg"),
        "和之前的牛相比，这些牛有什么特点？",
        "如果我想小规模养殖，你有什么建议？",
        "这两种牛哪种更适合初学者养殖？",
        "谢谢你的建议"
    ]
    
    for i, user_input in enumerate(conversation_flow, 1):
        print(f"\n{'=' * 80}")
        print(f"对话轮次 {i}/{len(conversation_flow)}")
        print(f"{'=' * 80}")
        print(f"用户> {user_input}")
        print(f"\n助手> ", end="", flush=True)
        
        try:
            # 调用 agent 并流式输出
            for chunk, metadata in cow_agent.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config,
                stream_mode="messages",
            ):
                # 只输出 AI 消息内容
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    print(chunk.content, end="", flush=True)
            
            print("\n")
            
            # 每次对话后稍作停顿
            if i < len(conversation_flow):
                time.sleep(1.5)
                
        except Exception as e:
            print(f"\n❌ 错误: {str(e)}\n")
            continue
    
    print("\n" + "=" * 80)
    print("复杂对话流程测试完成！")
    print("=" * 80)


def main():
    """主函数"""
    try:
        # 测试图片识别后的追问功能
        test_image_follow_up_questions()
        
        # 测试多图片连续对话能力
        test_multi_image_conversation()
        
        # 测试复杂对话流程
        test_complex_conversation_flow()
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
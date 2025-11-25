from dotenv import load_dotenv
load_dotenv()  # 加载 .env

from src.agents.cow_detection_agent import agent

def chat_with_agent(user_input: str, thread_id: str = "default") -> str:
    """与agent进行对话"""
    config = {"configurable": {"thread_id": thread_id}}
    
    result = ""
    for chunk, _ in agent.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="messages",
    ):
        # 只输出 AI 消息
        if type(chunk).__name__ == "AIMessageChunk" and chunk.content:
            result += chunk.content
    
    return result

def main():
    print("牛检测AI助手已启动，输入'退出'或'quit'结束对话")
    print("=" * 50)
    
    while True:
        user_input = input("用户> ")
        if user_input.lower() in ['退出', 'quit', 'exit']:
            print("助手> 再见！")
            break
            
        response = chat_with_agent(user_input)
        print(f"助手> {response}")
        
if __name__ == "__main__":
    main()

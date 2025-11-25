from dotenv import load_dotenv
import sys

print("正在启动系统...")
load_dotenv()  # 加载 .env

print("正在加载 AI 模型和工具...")
sys.stdout.flush()

from src.agents import pest_detection_agent
from src.agents import rice_detection_agent
from langchain_core.messages import HumanMessage, AIMessageChunk

print("✓ 系统加载完成！\n")

def main():
    config = {"configurable": {"thread_id": "1"}}
    
    while True:
        user_input = input("用户> ")
        print("助手> ", end="", flush=True)
        for chunk, metadata in pest_detection_agent.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config,
            stream_mode="messages",
        ):
            # 只输出 AI 消息，过滤掉工具消息和用户消息
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                print(chunk.content, end="", flush=True)
        print("\n")
        
        
if __name__ == "__main__":
    main()

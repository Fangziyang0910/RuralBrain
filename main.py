from dotenv import load_dotenv
load_dotenv()  # 加载 .env

from src.agents import pest_detection_agent
from src.agents import rice_detection_agent

def main():
    config = {"configurable": {"thread_id": "1"}}
    
    while True:
        user_input = input("用户> ")
        print("助手> ", end="", flush=True)
        for chunk, metadata in pest_detection_agent.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config,
            stream_mode="messages",
        ):
            # 只输出 AI 消息，过滤掉工具消息和用户消息
            if type(chunk).__name__ == "AIMessageChunk" and chunk.content:
                print(chunk.content, end="", flush=True)
        print("\n")
        
    # while True:
    #     user_input = input("用户> ")
    #     print("助手> ", end="", flush=True)
    #     for chunk, metadata in rice_detection_agent.stream(
    #         {"messages": [{"role": "user", "content": user_input}]},
    #         config,
    #         stream_mode="messages",
    #     ):
    #         # 只输出 AI 消息，过滤掉工具消息和用户消息
    #         if type(chunk).__name__ == "AIMessageChunk" and chunk.content:
    #             print(chunk.content, end="", flush=True)
    #     print("\n")
        
if __name__ == "__main__":
    main()

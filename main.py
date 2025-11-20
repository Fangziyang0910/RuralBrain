from dotenv import load_dotenv
load_dotenv()  # 加载 .env

from src.agents.pest_detection_agent import agent

def main():
    config = {"configurable": {"thread_id": "1"}}
    
    # print("助手> ", end="", flush=True)
    # for chunk, _ in agent.stream(
    #     {"messages": [{"role": "user", "content": "你好"}]},
    #     config,
    #     stream_mode="messages",
    # ):
    #     print(chunk.content, end="", flush=True)
    # print("\n")
    
    while True:
        user_input = input("用户> ")
        print("助手> ", end="", flush=True)
        for chunk, _ in agent.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config,
            stream_mode="messages",
        ):
            print(chunk.content, end="", flush=True)
        print("\n")
        
if __name__ == "__main__":
    main()

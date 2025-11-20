from dotenv import load_dotenv
load_dotenv()  # 加载 .env

from src.agents.pest_detection_agent import agent

def main():
    print("助手> ", end="", flush=True)
    for event in agent.stream({"messages": [{"role": "user", "content": "你好"}]}, stream_mode="messages"):
        msg = event[0]
        if hasattr(msg, "content") and msg.content:
            print(msg.content, end="", flush=True)
    print("\n")
    
    while True:
        user_input = input("用户> ")
        print("助手> ", end="", flush=True)
        for event in agent.stream({"messages": [{"role": "user", "content": user_input}]}, stream_mode="messages"):
            msg = event[0]
            if hasattr(msg, "content") and msg.content:
                print(msg.content, end="", flush=True)
        print("\n")
        
if __name__ == "__main__":
    main()

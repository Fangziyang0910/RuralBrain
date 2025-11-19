from src.agents.pest_detection_agent import agent

def main():
    print("助手> ")
    response = agent.invoke({"messages": [{"role": "user", "content": "你好"}]})
    print(response["messages"][-1].content)
    while True:
        user_input = input("用户> ")
        print("助手> ")
        response = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
        print(response["messages"][-1].content)
        
if __name__ == "__main__":
    main()

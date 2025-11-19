from src.agents.pest_detection_agent import agent

def main():
    response = agent.invoke({"messages": [{"role": "user", "content": "你好"}]})
    print(response["messages"][-1].content)

if __name__ == "__main__":
    main()

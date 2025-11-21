from dotenv import load_dotenv
load_dotenv()  # 加载 .env

from cow_detection_agent import chat_with_agent

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

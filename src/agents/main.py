# 文件名: src/main.py
import uuid
import os
import warnings
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessageChunk

from agents.rice_detecition_agent import agent

# 忽略警告配置
warnings.filterwarnings("ignore", category=DeprecationWarning, module='pydantic.v1')
warnings.filterwarnings("ignore", category=UserWarning, message=".*LangSmith now uses UUID v7.*")

def main():
    # --- 环境初始化 ---
    load_dotenv()
    os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "RuralBrain_Rice_Expert")

    print("--- 乡村振兴大脑 (大米专家版) ---")
    
    # 生成临时会话 ID
    conversation_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": conversation_id}}
    
    # --- 对话循环 ---
    while True:
        try:
            user_input = input("\n用户> ")
            if user_input.lower() in ["退出", "exit"]:
                print("再见！")
                break
            
            print("专家> ", end="", flush=True)
            
            # 使用流式输出
            for chunk, _ in agent.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config,
                stream_mode="messages"
            ):
                # 过滤并打印 AI 的回答
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    print(chunk.content, end="", flush=True)
                    
            print("\n") # 对话结束后换行
            
        except Exception as e:
            print(f"\n发生错误: {e}")
            # 调试时可以打开下面两行
            # import traceback
            # traceback.print_exc()

if __name__ == "__main__":
    main()
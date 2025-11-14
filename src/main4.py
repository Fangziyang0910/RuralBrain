import os
from dotenv import load_dotenv

# 1. 导入必要的模块
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

# 从你的工具文件中导入真实的工具类
from tools.rice_tool_api import RiceRecognitionApiTool

# 2. 初始化设置
load_dotenv()
llm = ChatDeepSeek(model="deepseek-chat", temperature=0)

# 使用你真实的工具
tools = [
    RiceRecognitionApiTool()
]

# 3. 创建 Agent Executor
# create_agent 直接返回我们需要的、可运行的 agent_executor
agent_executor = create_agent(llm, tools)

# 4. 主执行函数
if __name__ == "__main__":
    print("--- 欢迎使用乡村振兴大脑 Agent (稳定版) ---")

    # 定义测试图片路径
    image_path_to_test = os.path.abspath("test_data/test_rice.jpg")
    user_question = f"你好，请帮我分析一下这张图片，我想知道它的大米品种构成。图片路径是：{image_path_to_test}"

    print(f"\n[用户指令]: {user_question}\n")

    try:
        # 调用 agent_executor，使用 invoke 方法和正确的输入格式
        result = agent_executor.invoke({
            "messages": [HumanMessage(content=user_question)]
        })

        print("\n--- Agent 成功返回结果 ---")
        # 打印完整的返回字典，便于观察和调试
        print("完整的返回结果: ", result)

        # 从返回字典中正确的 "messages" 键里拿出最后一条消息的内容
        final_answer = result["messages"][-1].content

        print("\n--- Agent 最终回答 ---")
        print(final_answer)

    except Exception as e:
        print(f"\n--- 发生错误 ---")
        print(f"运行 Agent 时出错: {e}")
# src/main.py

import os
from dotenv import load_dotenv

# 1. 导入必要的模块
# LLM
from langchain_deepseek import ChatDeepSeek
# Agent 和执行器
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_agent.agent_executor import AgentExecutor
# Prompt 模板
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# 我们的两个工具
from tools.rice_tool import RiceRecognitionTool
from tools.rice_tool_api import RiceRecognitionApiTool

# 2. 初始化设置
# 加载 .env 文件中的环境变量 (DEEPSEEK_API_KEY)
load_dotenv()

# 初始化大语言模型 (LLM)
# temperature=0 表示我们希望模型的输出更具确定性，减少随机性
llm = ChatDeepSeek(model="deepseek-chat", temperature=0)

# 初始化我们的工具箱
# Agent 会根据任务描述，从这个列表中选择合适的工具
tools = [
    RiceRecognitionTool(),  # 方法二：本地函数调用工具
    RiceRecognitionApiTool()  # 方法一：远程API调用工具
]

# 3. 创建 Agent 的 Prompt
# 这是我们与 Agent 沟通的核心，定义了它的思考方式
# ChatPromptTemplate.from_messages 可以构建一个对话式的 prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的农业助手。你的任务是根据用户的请求，利用你所拥有的工具来分析图像并回答问题。"),
    ("human", "{input}"),  # 用户的输入
    # MessagesPlaceholder 是一个特殊的占位符，
    # 它会把 Agent 的思考过程（中间步骤）自动插入到这里
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 4. 创建 Agent
# create_tool_calling_agent 是一个高级函数，它将 LLM、工具和 Prompt 粘合在一起
# 生成的 Agent 知道如何根据 Prompt 的指示，利用 LLM 的思考能力来调用工具
agent = create_tool_calling_agent(llm, tools, prompt)

# 5. 创建 Agent 执行器 (Executor)
# Agent Executor 负责实际执行 Agent 的决策循环
# 它接收 Agent 的决策，调用工具，并将工具的返回结果再交给 Agent，如此往复直到任务完成
# verbose=True 会打印出 Agent 的完整思考过程，对于调试和理解至关重要！
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 6. 主执行函数
if __name__ == "__main__":
    print("--- 欢迎使用乡村振兴大脑 Agent ---")

    # 构建指向测试图片的绝对路径，这对工具的稳定运行很重要
    image_path_to_test = os.path.abspath("../test_data/test_rice.jpg")

    # --- 任务指令 ---
    # 这就是我们向 Agent 下达的自然语言指令
    user_question = f"你好，请帮我分析一下这张图片，我想知道它的大米品种构成。图片路径是：{image_path_to_test}"

    # 如果你想测试 API Tool，可以换成下面这条指令
    # user_question = f"你好，请使用网络API工具帮我分析这张图片，我想知道它的大米品种构成。图片路径是：{image_path_to_test}"

    print(f"\n[用户指令]: {user_question}\n")

    # 调用 Agent 执行器，开始处理任务
    result = agent_executor.invoke({
        "input": user_question
    })

    print("\n--- Agent 最终回答 ---")
    print(result["output"])

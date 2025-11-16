import os
from dotenv import load_dotenv

# 1. 导入必要的模块
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 从你的工具文件中导入真实的工具类
from tools.rice_tool_api import RiceRecognitionApiTool

# 2. 初始化设置
load_dotenv()

# 设置 LangSmith 追踪 (注意：我们现在用 getenv 从环境中读取)
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true") # 如果没读到，默认设为true
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "RuralBrain") # 如果没读到，默认设为RuralBrain

# 使用你真实的工具
tools = [
    RiceRecognitionApiTool()
]

llm = ChatDeepSeek(model="deepseek-chat", temperature=0, streaming=True)

# 3. 【关键步骤】创建包含强大系统指令的 Prompt 模板
# 这是告诉 Agent 行为准则的“紧箍咒”
prompt = (
       "你是一个名为'乡村振兴大脑'的AI工具调用助手，你的唯一使命是根据用户请求，精确地调用已提供的工具来完成任务。"
    "你的行为准则如下，你必须无条件遵守：\n"
    "1. **禁止对话**：你不是一个聊天机器人，不要与用户进行任何形式的对话、澄清或反问。你的任务是执行，而不是沟通。\n"
    "2. **工具优先**：分析用户意图，如果与提供的工具功能匹配，必须立即、直接地调用该工具。\n"
    "3. **精确匹配**：严格按照工具的描述来理解其功能。例如，如果一个工具的描述是'识别大米品种分类'，那么你就只能用它来做品种分类，不要猜测或扩展出'新旧识别'等不存在的功能。\n"
    "4. **后果警告**：任何对用户的反问行为，都将被视为一次严重的任务失败。你的目标是零反问、百分百工具调用。"
    "5. **总结结果**：在成功调用工具并获得结果后，你必须用自然、友好的语言对工具返回的'分析摘要'进行总结，然后将这个总结作为你的最终回答。"
    )

# 4. 创建 Agent 
agent_executor = create_agent(llm, tools)

# 4. 主执行函数
if __name__ == "__main__":
    print("--- 欢迎使用乡村振兴大脑 Agent (稳定版) ---")

    # 定义测试图片路径
    image_path_to_test = os.path.abspath("test_data/test_rice.jpg")
    user_question = f"你好，请帮我分析一下这张图片，我想知道它的大米品种构成。图片路径是：{image_path_to_test}"

    print(f"\n[用户指令]: {user_question}\n")

    try:
        input_data = {
          "messages": [
            SystemMessage(content=prompt), 
            HumanMessage(content=user_question)
           ]
        }

        final_answer = ""

        print("\n--- Agent 最终回答 (流式输出) ---")
        
        # 遍历 stream 输出的每一个数据块
        for chunk in agent_executor.stream(input_data):
            # 检查这个数据块是否是模型输出
            if "model" in chunk:
                # 获取模型输出的消息列表中的第一条消息
                message = chunk["model"]["messages"][0]
                
                # 【关键判断】
                # 如果这条消息是 AIMessage 并且它不是一个工具调用...
                # 那么它就是我们想要的最终回答！
                if isinstance(message, AIMessage) and not message.tool_calls:
                    # 以流式打印其内容
                    print(message.content, end="", flush=True)
                    # 拼接成完整回答
                    final_answer += message.content
        
        print("\n") # 流式结束后换行


    except Exception as e:
        print(f"\n--- 发生错误 ---")
        print(f"运行 Agent 时出错: {e}")
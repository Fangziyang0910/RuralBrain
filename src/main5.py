# 文件名: main5.py (无 Checkpoint, 内存级多轮对话版)
import uuid
import os
from dotenv import load_dotenv
import operator
from typing import TypedDict, Annotated, Sequence

# 1. 导入必要的模块 (已移除所有 checkpoint 相关导入)
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver

# 从你的工具文件中导入真实的工具类
from tools.rice_tool_api import RiceRecognitionApiTool

# --- 初始化与环境设置 ---
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "RuralBrain_InMemory_Stateful")

# --- 核心组件设置 ---
tools = [RiceRecognitionApiTool()]
llm = ChatDeepSeek(model="deepseek-chat", temperature=0)
llm_with_tools = llm.bind_tools(tools)

# --- 定义 Agent 的状态 (保持不变) ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# --- 定义图的节点和边 (保持不变) ---
def call_model(state):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def should_continue(state):
    if state["messages"][-1].tool_calls:
        return "continue"
    else:
        return "end"

# --- 构建图 (保持不变) ---
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", ToolNode(tools))
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"continue": "action", "end": END})
workflow.add_edge("action", "agent")

# 【【【 核心修改: 移除了 Checkpointer 】】】
# 我们现在编译一个纯净的、无状态保存的图
app = workflow.compile()

# 【【【 核心：在这里加上我们找到的 InMemorySaver 作为 Checkpointer 】】】
memory = InMemorySaver()
app = workflow.compile(checkpointer=memory)

# --- 主执行函数 ---
if __name__ == "__main__":
    print("--- 欢迎使用乡村振兴大脑 Agent (内存级多轮对话版) ---")
    
    # 随机生成一个对话ID
    conversation_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": conversation_id}}
    print(f"\n已开启新对话，ID (thread_id): {conversation_id}\n")

    prompt = (
        "你是一个名为'乡村振兴大脑'的AI工具调用助手，你的唯一使命是根据用户请求，精确地调用已提供的工具来完成任务。"
        "你的行为准则如下，你必须无条件遵守：\n"
        "1. **禁止对话**：你不是一个聊天机器人，不要与用户进行任何形式的对话、澄清或反问。你的任务是执行，而不是沟通。\n"
        "2. **工具优先**：分析用户意图，如果与提供的工具功能匹配，必须立即、直接地调用该工具。\n"
        "3. **自主执行 (最重要！)**：一旦确定工具和参数，你必须立即执行，严禁在执行前向用户进行任何形式的确认、检查或征求许可。你的任务是执行，不是寻求批准。即使是访问本地文件路径，也必须直接执行。\n"
        "4. **精确匹配**：严格按照工具的描述来理解其功能。\n"
        "5. **总结结果**：在成功调用工具并获得结果后，你必须用自然、友好的语言对工具返回的'分析摘要'进行总结，作为你的最终回答。"
    )

    is_first_turn = True # 用一个标志位来判断是否是第一轮对话

    while True:
        user_input = input("请输入您的指令 (输入 '退出' 来结束对话): ")
        if user_input.lower() == "退出":
            print("感谢使用，对话结束！")
            break
        print("---")
        
        # 【核心修改】输入永远只包含当前用户的最新消息
        # 在第一轮对话时，我们把 System Prompt 和 HumanMessage 一起发过去
        if is_first_turn:
            messages_to_send = [
                SystemMessage(content=prompt),
                HumanMessage(content=user_input)
            ]
            is_first_turn = False
        else:
            # 在后续对话中，只发送用户的最新消息
            messages_to_send = [HumanMessage(content=user_input)]

        inputs = {"messages": messages_to_send}
        
        print("Agent 正在思考...")
        print("\n--- Agent 最终回答 ---")
        
       # LangGraph 会自动根据 thread_id 加载历史，并将我们的新输入追加进去
        final_state = app.invoke(inputs, config=config)
        
        final_answer_message = final_state["messages"][-1]
        print(final_answer_message.content)
        
        print("\n\n")
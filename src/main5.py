# 文件名: main5.py (无 Checkpoint, 内存级多轮对话版)

import os
from dotenv import load_dotenv
import operator
from typing import TypedDict, Annotated, Sequence

# 1. 导入必要的模块 (已移除所有 checkpoint 相关导入)
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

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

# --- 主执行函数 ---
if __name__ == "__main__":
    print("--- 欢迎使用乡村振兴大脑 Agent (内存级多轮对话版) ---")

    # 【【【 核心修改: 我们在主循环中手动管理对话历史 】】】
    conversation_history = []

    while True:
        user_input = input("请输入您的指令 (输入 '退出' 来结束对话): ")
        if user_input.lower() == "退出":
            print("感谢使用，对话结束！")
            break
        print("---")
        
        # 1. 将新输入加入历史
        conversation_history.append(HumanMessage(content=user_input))
        
        # 2. 将当前全部历史作为输入
        inputs = {"messages": conversation_history}
        
        print("Agent 正在思考...")
        print("\n--- Agent 最终回答 ---")
        
        # 3. 调用 invoke 获取最终状态
        # 因为没有流式 checkpoint，我们用 invoke 更简单直接
        final_state = app.invoke(inputs)
        
        # 4. 从最终状态中提取并打印最后一条消息
        final_answer_message = final_state["messages"][-1]
        print(final_answer_message.content)
        
        # 5. 将模型的最终回答也加入历史，为下一轮做准备
        conversation_history.append(final_answer_message)
        
        print("\n\n")
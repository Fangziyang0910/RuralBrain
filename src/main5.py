# 文件名: main5.py (无 Checkpoint, 内存级多轮对话版)
import uuid
import os
from dotenv import load_dotenv
import operator
from typing import TypedDict, Annotated, Sequence
import warnings

# 1. 导入必要的模块 (已移除所有 checkpoint 相关导入)
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# 从你的工具文件中导入真实的工具类
from tools.rice_tool_api import RiceRecognitionApiTool

# 这行代码会忽略所有来自 Pydantic V1 的废弃警告，从而清理输出
warnings.filterwarnings("ignore", category=DeprecationWarning, module='pydantic.v1')
# 新增这行来忽略关于 LangSmith UUID v7 的特定 UserWarning
warnings.filterwarnings("ignore", category=UserWarning, message=".*LangSmith now uses UUID v7.*")

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


# 2. 创建一个连接到本地数据库文件的 saver
#    这会在你的项目目录下创建一个名为 "checkpoints.sqlite" 的文件来存储所有对话历史
memory = SqliteSaver.from_conn_string("checkpoints.sqlite")

# 3. 编译时使用新的持久化 saver
app = workflow.compile(checkpointer=memory)

# --- 主执行函数 ---
if __name__ == "__main__":
    # 使用 'with' 语句来正确管理数据库连接
    # 这会将真正的 saver 对象赋给 memory，并在代码块结束时自动关闭连接
    with SqliteSaver.from_conn_string("checkpoints.sqlite") as memory:

        # 将 app 的编译移到 with 代码块内部
        app = workflow.compile(checkpointer=memory)
        print("--- 欢迎使用乡村振兴大脑 Agent (内存级多轮对话版) ---")
    
        # 【【【 核心修复 2: 实现对话选择功能 】】】
        conversation_id = None
    
        while not conversation_id:
            choice = input("\n请选择操作: (1) 开启新对话 (2) 继续旧对话: ")
            if choice == "1":
                conversation_id = str(uuid.uuid4())
                print(f"\n已开启新对话，请记下您的对话ID (thread_id): {conversation_id}\n")
            elif choice == "2":
                saved_id = input("请输入您想继续的对话 thread_id: ")
                if saved_id:
                    conversation_id = saved_id
                    print(f"\n已继续对话，ID (thread_id): {conversation_id}\n")
                else:
                    print("无效的ID，请重新选择。")
            else:
                print("无效输入，请输入 1 或 2。")

        config = {"configurable": {"thread_id": conversation_id}}
    
        # 检查恢复的对话是否是全新的，用于决定是否发送系统提示词
        # 我们通过检查 checkpointer 中是否已有该 ID 的历史来判断
        is_new_conversation = not memory.get(config)

        prompt = (
            "你是一个名为'乡村振兴大脑'的AI工具调用助手，你的唯一使命是根据用户请求，精确地调用已提供的工具来完成任务。"
            "你的行为准-则如下，你必须无条件遵守：\n"
            "1. **禁止对话**：你不是一个聊天机器人，不要与用户进行任何形式的对话、澄清或反问。你的任务是执行，而不是沟通。\n"
            "2. **工具优先**：分析用户意图，如果与提供的工具功能匹配，必须立即、直接地调用该工具。\n"
            "3. **自主执行 (最重要！)**：一旦确定工具和参数，你必须立即执行，严禁在执行前向用户进行任何形式的确认、检查或征求许可。你的任务是执行，不是寻求批准。即使是访问本地文件路径，也必须直接执行。\n"
            "4. **精确匹配**：严格按照工具的描述来理解其功能。\n"
            "5. **总结结果**：在成功调用工具并获得结果后，你必须用自然、友好的语言对工具返回的'分析摘要'进行总结，作为你的最终回答。"
        )

        while True:
            user_input = input("请输入您的指令 (输入 '退出' 来结束对话): ")
            if user_input.lower() == "退出":
                print("感谢使用，对话结束！")
                break
            print("---")
            
            # 只有在这是一个全新的对话的第一轮时，才发送系统提示词
            if is_new_conversation:
                messages_to_send = [
                    SystemMessage(content=prompt),
                    HumanMessage(content=user_input)
                ]
                is_new_conversation = False # 后续不再是新对话
            else:
                messages_to_send = [HumanMessage(content=user_input)]

            inputs = {"messages": messages_to_send}
            
            print("Agent 正在思考...")
            print("\n--- Agent 最终回答 ---")
            
            final_answer_message = None
            for event in app.stream(inputs, config=config, stream_mode="updates"):
                if "agent" in event:
                    final_answer_message = event["agent"]["messages"][-1]
            
            if final_answer_message:
                print(final_answer_message.content)
            
            print("\n")
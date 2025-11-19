# 文件名: src/main_simple.py
import uuid
import os
from dotenv import load_dotenv
import warnings

# 1. 导入必要模块
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

# 导入工具
from tools.rice_tool_func import rice_recognition_tool

# 忽略警告
warnings.filterwarnings("ignore", category=DeprecationWarning, module='pydantic.v1')
warnings.filterwarnings("ignore", category=UserWarning, message=".*LangSmith now uses UUID v7.*")

# --- 初始化 ---
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
# 修改Project名以便区分
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "RuralBrain_Simple_React")

# --- 核心组件设置 ---
tools = [rice_recognition_tool]
llm = ChatDeepSeek(model="deepseek-chat", temperature=0)
memory = InMemorySaver()

# 系统提示词内容
SYSTEM_PROMPT_TEXT = (
    "你是一个名为'乡村振兴大脑'的AI工具调用助手，你的唯一使命是根据用户请求，精确地调用已提供的工具来完成任务。"
    "你的行为准则如下，你必须无条件遵守：\n"
    "1. **禁止对话**：你不是一个聊天机器人，不要与用户进行任何形式的对话、澄清或反问。你的任务是执行，而不是沟通。\n"
    "2. **工具优先**：分析用户意图，如果与提供的工具功能匹配，必须立即、直接地调用该工具。\n"
    "3. **自主执行**：一旦确定工具和参数，你必须立即执行，严禁在执行前向用户进行任何形式的确认。本地文件路径请直接读取。\n"
    "4. **总结结果**：工具调用成功后，用自然、友好的语言总结'分析摘要'作为最终回答。"
)

# --- 【核心重构】 ---
# 1. 去掉了报错的 state_modifier/messages_modifier 参数
# 这样无论哪个版本的 langgraph 都能兼容
app = create_react_agent(model=llm, tools=tools, checkpointer=memory)


# --- 主执行函数 ---
if __name__ == "__main__":
    print("--- 欢迎使用乡村振兴大脑 Agent (极简版 / 内存记忆) ---")
    
    conversation_id = None
    while not conversation_id:
        choice = input("\n请选择操作: (1) 开启新对话 (2) 继续旧对话(仅本次运行有效): ")
        if choice == "1":
            conversation_id = str(uuid.uuid4())
            print(f"\n已开启新对话 ID: {conversation_id}")
        elif choice == "2":
            saved_id = input("请输入 thread_id: ")
            if saved_id:
                conversation_id = saved_id
                print(f"\n已继续对话 ID: {conversation_id}")
            else:
                print("无效输入")
        else:
            print("无效输入")

    config = {"configurable": {"thread_id": conversation_id}}

    # 检查是否是新对话（通过检查内存中是否有历史记录）
    # 如果是新对话，我们需要手动发送 System Prompt
    current_state = app.get_state(config)
    is_first_turn = len(current_state.values) == 0

    while True:
        user_input = input("\n请输入指令 (输入 '退出' 结束): ")
        if user_input.lower() == "退出":
            print("再见！")
            break
        print("--- Agent 正在思考...")
        
        messages_to_send = []
        
        # 【关键修改】手动注入 System Prompt
        # 只有在对话的第一轮，我们将 SystemMessage 插在最前面
        if is_first_turn:
            messages_to_send.append(SystemMessage(content=SYSTEM_PROMPT_TEXT))
            is_first_turn = False # 标记后续不再发送 System Prompt
            
        messages_to_send.append(HumanMessage(content=user_input))
        
        inputs = {"messages": messages_to_send}
        
        final_answer = None
        try:
            for event in app.stream(inputs, config=config, stream_mode="updates"):
                if "agent" in event:
                    last_msg = event["agent"]["messages"][-1]
                    final_answer = last_msg.content
            
            if final_answer:
                print(f"\n--- Agent 回答 ---\n{final_answer}")
            else:
                print("(Agent 执行完成，但未生成文本，可能是正在调用工具...)")
                
        except Exception as e:
            print(f"发生错误: {e}")
            # 打印详细错误以便调试
            import traceback
            traceback.print_exc()
# 文件名: src/main_simple.py
import uuid
import os
from dotenv import load_dotenv
import warnings

# 1. 导入必要模块
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import AIMessageChunk

# 导入工具
from tools.rice_detection_tool import rice_recognition_tool

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

# --- 新的系统提示词 (XML结构) ---
SYSTEM_PROMPT = """
<role>
你是一位资深的大米鉴定与农业专家，专注于大米品种识别与品质评估。你不仅能识别大米，还能根据其品种提供烹饪建议和储存知识。
</role>

<tools>
你可以使用以下工具：
- rice_recognition_tool：调用视觉识别服务，分析大米图片的品种
  - 输入：图片文件路径
  - 输出：识别到的品种名称、置信度/数量统计
</tools>

<task>
当用户提供图片时，请按以下流程工作：
1. **响应请求**：礼貌地告知用户正在开始识别。
2. **调用工具**：使用 rice_recognition_tool 进行分析。
3. **解读结果**：根据工具返回的品种信息，向用户确认识别结果。
4. **专家建议**：
   - 介绍该品种大米的口感特点（如：软糯、Q弹、有嚼劲）。
   - 推荐最佳烹饪方式（如：煮粥、炒饭、做寿司）。
   - (可选) 简单的储存建议。
</task>

<constraints>
- 保持专业、亲切的语气。
- 如果工具识别失败或结果不明确，请诚实告知用户并建议重试。
- 不要捏造事实，仅基于工具返回的结果扩展相关农业知识。
</constraints>
"""


agent = create_agent(
    model=llm, 
    tools=tools, 
    checkpointer=memory,
    system_prompt=SYSTEM_PROMPT # LangGraph 新版推荐写法，替代 system_message
)


# --- 主执行函数 ---
if __name__ == "__main__":
    print("--- 乡村振兴大脑 (大米专家版) ---")
    
    # 生成临时会话 ID
    conversation_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": conversation_id}}
    
    while True:
        user_input = input("\n用户> ")
        if user_input.lower() in ["退出", "exit"]:
            print("再见！")
            break
        
        print("专家> ", end="", flush=True)
        
        try:
            # --- 核心修改：更稳健的流式输出循环 ---
            for chunk, _ in agent.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config,
                stream_mode="messages"
            ):
                # 1. 判断是否为 AI 回复的片段 (AIMessageChunk)
                # 2. 并且内容不能为空 (过滤掉工具调用产生的空内容片段)
                if isinstance(chunk, AIMessageChunk) and chunk.content:
                    print(chunk.content, end="", flush=True)
                    
            print("\n") # 对话结束后换行
            
        except Exception as e:
            print(f"\n发生错误: {e}")
            import traceback
            traceback.print_exc()
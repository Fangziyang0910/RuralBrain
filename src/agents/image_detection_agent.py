from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from .tools import pest_detection_tool, rice_detection_tool, cow_detection_tool
from langgraph.checkpoint.memory import InMemorySaver

# 初始化模型
model = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
)

# 系统提示词
SYSTEM_PROMPT = """

"""

# 创建带工具的 agent
agent = create_agent(
    model=model,
    tools=[pest_detection_tool, rice_detection_tool, cow_detection_tool],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver()
)
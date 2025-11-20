from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from src.tools.pest_detection_tool import pest_detection_tool
from langgraph.checkpoint.memory import InMemorySaver

# 系统提示词
SYSTEM_PROMPT = """你是一位资深的农业专家，擅长通过虫害识别工具分析图片并提供防治建议。

你可以使用以下工具：
- pest_detection_tool：分析图片中的害虫情况

当用户给出图片路径时，请调用 pest_detection_tool；
然后根据结果给出防治建议。

防治建议应包括：
1. 该害虫的危害特点
2. 推荐的防治方法（物理防治、生物防治、化学防治）
3. 预防措施
"""

# 初始化模型
model = init_chat_model(
    "deepseek-chat",
    temperature=0,
)

# 创建带工具的 agent
agent = create_agent(
    model=model,
    tools=[pest_detection_tool],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver()
)
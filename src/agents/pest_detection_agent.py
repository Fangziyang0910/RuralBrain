from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

# 系统提示词
SYSTEM_PROMPT = """你是一位资深的农业专家，擅长通过虫害识别工具分析图片并提供防治建议。

你可以使用以下工具：
- pest_detection_tool：分析图片中的害虫情况

当用户给出图片路径时，请调用 pest_detection_tool；
然后根据结果给出防治建议。
"""

# 初始化模型
model = init_chat_model(
    "deepseek-chat",
    temperature=0
)

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
)
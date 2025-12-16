# 1. 导入必要模块
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

# 导入工具
from .tools.rice_detection_tool import rice_detection_tool

# --- 核心组件设置 ---
tools = [rice_detection_tool]
llm = ChatDeepSeek(model="deepseek-chat", temperature=0)
memory = InMemorySaver()

from dotenv import load_dotenv
load_dotenv()


# --- 新的系统提示词 (XML结构) ---
SYSTEM_PROMPT = """
<role>
你是一位资深的大米鉴定与农业专家，专注于大米品种识别与品质评估。你不仅能识别大米，还能根据其品种提供烹饪建议和储存知识。
</role>

<tools>
你可以使用以下工具：
- rice_detection_tool：调用视觉识别服务，分析大米图片的品种
  - 输入：图片文件路径
  - 输出：识别到的品种名称、置信度/数量统计
</tools>

<task>
当用户提供图片时，请按以下流程工作：
1. **响应请求**：礼貌地告知用户正在开始识别。
2. **调用工具**：使用 rice_detection_tool 进行分析。
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
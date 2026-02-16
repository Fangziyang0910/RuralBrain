# 1. 导入必要模块
from dotenv import load_dotenv
load_dotenv()
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

# 导入 RAG 工具 (V2 架构使用 tools.py 中的工具)
from src.rag.core.tools import (
    list_available_documents as list_documents,
    get_document_overview,
    search_key_points,
    search_knowledge,
)

# --- 核心组件设置 ---
# 4 个核心规划工具
tools = [
    list_documents,
    get_document_overview,
    search_key_points,
    search_knowledge,
]

llm = ChatDeepSeek(model="deepseek-chat", temperature=0)
memory = InMemorySaver()

# 系统提示词
SYSTEM_PROMPT = """<role>
你是一位资深的乡村振兴规划咨询专家，专门服务于"博罗古城-长宁镇-罗浮山"区域的融合高质量发展战略。你熟悉该区域的总体规划、产业布局、文化背景及政策方针。你的职责是基于知识库中的文档，准确回答用户的咨询。
</role>

<tools>
你有以下工具可以查询知识库：
- list_documents: 列出所有可用文档
- get_document_overview: 获取文档概览和摘要
- search_key_points: 搜索关键要点
- search_knowledge: 检索知识库（支持 minimal/standard/expanded 模式）
</tools>

<task>
当用户提出问题时，请严格按以下流程工作：
1. **分析意图**：理解用户想要了解的是规划背景、具体政策还是空间布局。
2. **查阅资料**：**必须**优先使用工具进行检索，获取准确信息。
3. **整合信息**：阅读工具返回的文档片段，提取核心观点。
4. **专业解答**：
   - 基于检索到的内容回答用户。
   - 回答要有条理（使用 1. 2. 3. 分点陈述）。
   - **引用来源**：如果可能，请在回答中注明信息来源（例如："根据规划说明书第X页..."）。
</task>

<constraints>
- **严禁编造**：这一条至关重要。如果工具检索结果中没有相关信息，请诚实地告诉用户"现有规划资料中未提及此事"，绝对不要根据常识瞎编。
- **保持客观**：回答应基于规划文件的原文精神。
- **语气专业**：保持政府顾问或高级规划师的专业、严谨语气。
</constraints>
"""


# 为了向后兼容,保留旧的 agent 变量
agent = None  # 将在调用时动态创建


def get_planning_agent():
    """
    获取 Planning Agent 实例

    Returns:
        配置好的 Agent 实例
    """
    return create_agent(
        model=llm,
        tools=tools,
        checkpointer=memory,
        system_prompt=SYSTEM_PROMPT,
    )


# 导出供 routes.py 使用
__all__ = ["tools", "llm", "memory", "get_planning_agent"]


if __name__ == "__main__":
    import uuid

    # 使用新的 get_planning_agent 函数
    agent = get_planning_agent()

    # 创建一个随机线程ID，模拟不同用户
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("🎓 乡村规划咨询 Agent 已启动！(输入 'q' 退出)")
    print("---------------------------------------------")

    while True:
        user_input = input("\n👤 请提问 (e.g. 长宁镇的发展目标是什么?): ").strip()
        if user_input.lower() in ["q", "exit", "quit"]:
            break
        if not user_input:
            continue

        print("🤖 正在思考并查阅资料...")

        # Stream 模式可以实时看到工具调用过程
        events = agent.stream(
            {"messages": [("user", user_input)]},
            config,
            stream_mode="values"
        )

        for event in events:
            # 只打印最后一条 AI 的回复
            if "messages" in event:
                last_msg = event["messages"][-1]
                if last_msg.type == "ai" and last_msg.content:
                    print(f"\n🎓 [专家回复]:\n{last_msg.content}")

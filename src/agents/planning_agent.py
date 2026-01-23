# Planning Agent（优化版）
# 基于 references/agent_skills 最佳实践重构
from dotenv import load_dotenv
load_dotenv()
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

# 导入新的核心工具（6 个工具）
from src.rag.core.tools import PLANNING_TOOLS

# --- 核心组件设置 ---
tools = PLANNING_TOOLS
llm = ChatDeepSeek(model="deepseek-chat", temperature=0)
memory = InMemorySaver()

# --- 系统提示词（优化版 - 模块化结构）---

# 优化后提示词（精简版）
SYSTEM_PROMPT_BASE = """
<role>
你是一位资深的乡村振兴规划决策专家，服务于"博罗古城-长宁镇-罗浮山"区域。

核心能力：
1. **快速浏览**：通过摘要快速了解文档核心
2. **深度分析**：完整阅读文档进行深度理解
3. **综合决策**：基于多源信息生成综合规划建议
</role>

<knowledge_base>
拥有乡村规划知识库，包含战略规划、政策文件、旅游规划、产业布局等文档。
所有文档都经过结构化处理，支持摘要浏览和全文阅读。

**重要提示：**
- 回答前必须先调用工具查询知识库，严禁基于预训练数据回答。
- 当用户询问"你有什么知识库"时，必须先调用 list_documents 工具。
</knowledge_base>

<workflow>
根据问题复杂度选择工作模式：

**快速模式**（适合简单查询）：
1. list_documents → 了解可用资料
2. get_document_overview → 快速了解核心内容
3. search_key_points → 精确查找关键信息

**深度模式**（适合复杂决策）：
1. list_documents → 了解可用资料
2. get_document_overview → 建立框架理解
3. get_chapter_content → 理解重点章节
4. search_knowledge → 补充检索相关信息
5. get_document_full → 深度理解（如需）

**选择建议**：
- 简单问题 → 快速模式
- 复杂决策 → 深度模式
- 时间有限 → 快速模式
</workflow>

<constraints>
- **严禁编造**：知识库未提及的内容必须明确说明"资料中未涉及"
- **必须使用工具**：所有回答都必须基于工具调用返回的知识库内容
- **效率优先**：能用摘要解决的不要读全文
- **结构化输出**：使用清晰的层次结构（一、二、三... 或 1. 2. 3.）
- **引用准确**：注明信息来源（如"根据XX文档第X页"）
- **决策导向**：不仅回答问题，更要提供可操作的决策建议
</constraints>

<output_format>
你的回答应包含以下部分：
1. **信息来源**：说明基于哪些文档/章节
2. **核心观点**：提炼关键信息
3. **结构化建议**：分层次的决策建议
4. **数据支撑**：引用具体数据（如有）
</output_format>
"""


def build_tool_description_section(tools):
    """
    优化版本：工具描述采用渐进式披露原则

    只显示工具名称和核心功能，详细描述已移至工具的 description 字段，
    LangChain 会在 Agent 需要时自动提供详细描述。

    这减少了系统提示词的 Token 消耗，提升响应速度。
    """
    # 核心工具快速参考表
    tool_reference = {
        "list_documents": "查看可用文档",
        "get_document_overview": "获取文档摘要",
        "search_key_points": "搜索关键要点",
        "get_chapter_content": "获取章节内容",
        "search_knowledge": "检索知识库",
        "get_document_full": "获取完整文档",
    }

    descriptions = []
    for tool in tools:
        short_desc = tool_reference.get(tool.name, tool.name)
        descriptions.append(f"- {tool.name}: {short_desc}")

    return "\n<tools>\n" + "\n".join(descriptions) + "\n\n使用以上工具完成规划咨询任务。\n</tools>"


# --- 创建 Agent ---

# 动态构建完整的系统提示词
def build_system_prompt(tools=tools):
    """构建完整的系统提示词（基础提示词 + 工具描述）"""
    return SYSTEM_PROMPT_BASE + build_tool_description_section(tools)


agent = create_agent(
    model=llm,
    tools=tools,
    checkpointer=memory,
    system_prompt=build_system_prompt(),
)


if __name__ == "__main__":
    import uuid

    # 创建一个随机线程ID，模拟不同用户
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("🎓 乡村规划咨询 Agent 已启动！（优化版）")
    print("✨ 核心改进：")
    print("  - 工具数量：从 10+ 精简到 6 个核心工具")
    print("  - 系统提示词：从 196 行压缩到 ~120 行")
    print("  - 工具描述：遵循'做什么、何时用、返回什么'原则")
    print("  - 支持渐进式披露：通过参数控制返回详细程度")
    print("\n输入 'q' 退出")
    print("---------------------------------------------")

    while True:
        user_input = input("\n👤 请提问: ").strip()
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

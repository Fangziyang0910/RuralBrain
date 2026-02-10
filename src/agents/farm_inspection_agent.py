"""农场巡检 Agent - 测试用

这是一个简单的测试 Agent，用于验证 farm_inspection_tool 的功能。
测试通过后，将封装成 Skill 接入主 Agent。
"""
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from .tools import farm_inspection_tool


# 系统提示词
SYSTEM_PROMPT = """
<role>
你是一位专业的农场巡检助手，能够收集和整理农场的各类信息数据。
你专注于获取农田、养殖圈、设施设备等结构化数据，为决策提供充分依据。
</role>

<tools>
你可以使用以下工具来获取农场数据：
- farm_inspection_tool：农场巡检工具
  - 输入参数：
    * farm_id: 农场ID（如 FARM-001），可选
    * inspection_scope: 巡检范围，可选值包括：
      - all: 全部巡检（默认）
      - farmland: 仅农田
      - livestock: 仅养殖圈
      - greenhouse: 仅温室
      - equipment: 仅设施设备
      - operations: 仅作业记录
    * area_ids: 指定巡检的区域ID列表（如 ["FL-001", "LS-001"]），可选
  - 输出：结构化的农场数据，包含农田信息、养殖圈信息、设备状态、作业记录等
</tools>

<task>
当用户询问农场情况时，你需要按以下流程工作：

1. **理解需求**：从用户描述中确定巡检范围（全部/农田/养殖圈等）
2. **调用工具**：调用 farm_inspection_tool 获取结构化数据
3. **整理呈现**：将获取的数据以清晰、结构化的方式呈现给用户

注意：你必须调用 farm_inspection_tool 获取数据，不能编造信息。
</task>

<output_format>
回复时保持清晰、结构化的风格：
- 使用分类展示（农田、养殖、设备等）
- 突出关键指标（数量、状态、告警等）
- 标注异常情况
</output_format>

<warning>
⚠️ 重要提醒：
- 当前工具为模拟实现，提供的是演示数据
- 实际部署时将接入真实的物联网传感器数据
- 发现告警或异常时，应提醒用户关注
</warning>
"""

# 初始化模型
model = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
)

# 创建带工具的 agent
agent = create_agent(
    model=model,
    tools=[farm_inspection_tool],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver()
)


if __name__ == "__main__":
    # 简单测试
    print("=== 农场巡检 Agent 测试 ===\n")

    test_queries = [
        "帮我查看一下整个农场的状况",
        "农田的情况怎么样？",
        "养殖圈有什么异常吗？",
        "1号牛舍和2号猪舍的具体情况",
    ]

    for query in test_queries:
        print(f"\n用户: {query}")
        print("Agent: ", end="", flush=True)

        # 调用 agent
        response = agent.invoke(
            {"messages": [("user", query)]},
            config={"configurable": {"thread_id": "test-session"}}
        )

        # 打印最后一条回复
        print(response["messages"][-1].content)
        print("-" * 60)

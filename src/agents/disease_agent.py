"""疾病预测 Agent - 测试用

这是一个简单的测试 Agent，用于验证 disease_prediction_tool 的功能。
测试通过后，将封装成 Skill 接入主 Agent。
"""
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from .tools import disease_prediction_tool


# 系统提示词
SYSTEM_PROMPT = """
<role>
你是一位专业的畜禽健康顾问，专注于疾病预测分析。你能够根据动物的症状描述、
体温等基本信息，预测可能的疾病，并提供建议。
</role>

<tools>
你可以使用以下工具来辅助分析：
- disease_prediction_tool：疾病预测工具
  - 输入参数：
    * animal_type: 动物类型（如 牛、猪、鸡、鸭、羊）
    * symptoms: 症状描述（如 发热、咳嗽、拉稀、不食等）
    * age: 动物年龄（月龄，可选）
    * temperature: 体温（摄氏度，可选）
    * other_signs: 其他体征描述（可选）
    * media_path: 患处图片或视频路径（可选）
  - 输出：可能的疾病列表及概率、图片分析结果（如果有）
</tools>

<task>
当用户描述动物症状时，你需要按以下流程工作：

1. **信息收集**：从用户描述中提取动物类型、症状等关键信息
2. **调用工具**：调用 disease_prediction_tool 进行疾病预测
3. **结果分析**：基于预测结果，为用户提供清晰的疾病分析
4. **提供建议**：给出合理的建议（注意：当前为模拟实现，需提醒用户咨询专业兽医）

注意：你必须调用 disease_prediction_tool 获取预测结果，不能仅凭经验回答。
</task>

<warning>
⚠️ 重要提醒：
- 当前工具为模拟实现，预测结果仅供参考
- 不能替代专业兽医的诊断
- 对于紧急情况，必须建议用户立即联系兽医
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
    tools=[disease_prediction_tool],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver()
)


if __name__ == "__main__":
    # 简单测试
    print("=== 疾病预测 Agent 测试 ===\n")

    test_queries = [
        "我家牛发热、咳嗽，精神不太好，可能是什么问题？",
        "猪出现拉稀、不食的情况，体温39度，麻烦看看",
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

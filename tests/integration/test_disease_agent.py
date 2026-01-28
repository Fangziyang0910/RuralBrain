"""疾病预测 Agent 集成测试

测试 disease_prediction_tool 在 Agent 环境中的工作情况。
"""
import pytest
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.disease_agent import agent


class TestDiseaseAgent:
    """测试疾病预测 Agent"""

    def test_basic_prediction(self):
        """测试基础疾病预测功能"""
        query = "我家牛发热、咳嗽，精神不太好，可能是什么问题？"

        response = agent.invoke(
            {"messages": [("user", query)]},
            config={"configurable": {"thread_id": "test-1"}}
        )

        assert response is not None
        assert "messages" in response
        assert len(response["messages"]) > 0

        # 最后一条消息是 Agent 的回复
        agent_reply = response["messages"][-1].content
        assert agent_reply is not None
        assert len(agent_reply) > 0

    def test_pig_diarrhea(self):
        """测试猪拉稀症状"""
        query = "猪出现拉稀、不食的情况，体温39度"

        response = agent.invoke(
            {"messages": [("user", query)]},
            config={"configurable": {"thread_id": "test-2"}}
        )

        agent_reply = response["messages"][-1].content
        assert agent_reply is not None

    def test_chicken_symptoms(self):
        """测试鸡类症状"""
        query = "鸡精神萎靡、羽毛蓬松，不吃东西"

        response = agent.invoke(
            {"messages": [("user", query)]},
            config={"configurable": {"thread_id": "test-3"}}
        )

        agent_reply = response["messages"][-1].content
        assert agent_reply is not None

    def test_multi_turn_conversation(self):
        """测试多轮对话"""
        thread_id = "test-conversation"

        # 第一轮
        response1 = agent.invoke(
            {"messages": [("user", "我家牛发热咳嗽")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        # 第二轮（继续同一个会话）
        response2 = agent.invoke(
            {"messages": [("user", "体温大约39.5度")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        assert response1 is not None
        assert response2 is not None

    def test_tool_was_called(self):
        """验证工具是否被正确调用"""
        query = "牛发热咳嗽，帮我预测一下可能是什么病"

        response = agent.invoke(
            {"messages": [("user", query)]},
            config={"configurable": {"thread_id": "test-tool-1"}}
        )

        # 检查是否有工具调用的记录
        messages = response["messages"]
        tool_called = False

        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_called = True
                # 验证调用的是正确的工具
                for call in msg.tool_calls:
                    assert "name" in call
                    # 应该调用 disease_prediction_tool

        # Agent 应该调用了工具
        assert tool_called, "Agent 应该调用 disease_prediction_tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

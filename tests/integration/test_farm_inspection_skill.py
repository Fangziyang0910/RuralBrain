"""农场巡检 Skill 集成测试

测试 farm_inspection Skill 在主 Agent (Orchestrator V2) 中的工作情况。
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

from src.agents.orchestrator_agent_v2 import agent


class TestFarmInspectionSkill:
    """测试农场巡检 Skill 在主 Agent 中的功能"""

    def test_full_farm_inspection_via_main_agent(self):
        """测试通过主 Agent 进行全农场巡检"""
        query = "帮我查看一下整个农场的状况"

        response = agent.invoke(
            {"messages": [("user", query)]},
            config={"configurable": {"thread_id": "test-skill-1"}}
        )

        assert response is not None
        assert "messages" in response

        agent_reply = response["messages"][-1].content
        assert agent_reply is not None
        assert len(agent_reply) > 0

    def test_farmland_inspection_via_main_agent(self):
        """测试通过主 Agent 进行农田巡检"""
        query = "农田的情况怎么样？"

        response = agent.invoke(
            {"messages": [("user", query)]},
            config={"configurable": {"thread_id": "test-skill-2"}}
        )

        agent_reply = response["messages"][-1].content
        assert agent_reply is not None

    def test_livestock_inspection_via_main_agent(self):
        """测试通过主 Agent 进行养殖圈巡检"""
        query = "养殖圈有什么异常吗？"

        response = agent.invoke(
            {"messages": [("user", query)]},
            config={"configurable": {"thread_id": "test-skill-3"}}
        )

        agent_reply = response["messages"][-1].content
        assert agent_reply is not None

    def test_equipment_status_via_main_agent(self):
        """测试通过主 Agent 查询设备状态"""
        query = "农场设备运行正常吗？"

        response = agent.invoke(
            {"messages": [("user", query)]},
            config={"configurable": {"thread_id": "test-skill-4"}}
        )

        agent_reply = response["messages"][-1].content
        assert agent_reply is not None

    def test_skill_was_loaded(self):
        """验证 Skill 是否被正确加载"""
        query = "帮我检查一下农田和养殖的情况"

        response = agent.invoke(
            {"messages": [("user", query)]},
            config={"configurable": {"thread_id": "test-skill-load-1"}}
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
                    # 应该调用 farm_inspection_tool

        # Agent 应该调用了工具
        assert tool_called, "Agent 应该调用 farm_inspection_tool"

    def test_multi_turn_with_skill(self):
        """测试多轮对话中 Skill 的使用"""
        thread_id = "test-skill-conversation"

        # 第一轮
        response1 = agent.invoke(
            {"messages": [("user", "农场设备状态如何？")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        # 第二轮（继续同一个会话）
        response2 = agent.invoke(
            {"messages": [("user", "有告警吗？")]},
            config={"configurable": {"thread_id": thread_id}}
        )

        assert response1 is not None
        assert response2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

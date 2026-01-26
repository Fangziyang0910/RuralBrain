"""
Orchestrator Agent V2 单元测试

测试 Skills 架构的 Orchestrator Agent V2 实现。
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.orchestrator_agent_v2 import agent, all_skills, orchestrator_tools
from src.agents.skills.orchestration_skills import create_all_orchestration_skills
from src.agents.skills.base import Skill


class TestOrchestrationSkills:
    """测试编排技能创建"""

    def test_skills_creation(self):
        """测试技能创建"""
        orchestration_skills = create_all_orchestration_skills()
        assert len(orchestration_skills) == 2
        assert orchestration_skills[0].name == "intent_recognition"
        assert orchestration_skills[1].name == "scenario_switching"

    def test_skill_types(self):
        """测试技能类型"""
        skills = create_all_orchestration_skills()
        for skill in skills:
            assert isinstance(skill, Skill)

    def test_skill_categories(self):
        """测试技能分类"""
        skills = create_all_orchestration_skills()
        for skill in skills:
            assert skill.category == "orchestration"

    def test_skill_prompt_addendum(self):
        """测试技能简短描述生成"""
        skills = create_all_orchestration_skills()
        for skill in skills:
            addendum = skill.get_prompt_addendum()
            assert skill.name in addendum
            assert skill.description in addendum
            assert "**" in addendum  # Markdown 格式

    def test_skill_full_content(self):
        """测试技能完整内容生成"""
        skills = create_all_orchestration_skills()
        for skill in skills:
            content = skill.get_full_content()
            assert skill.name in content
            assert skill.system_prompt in content
            assert "##" in content  # Markdown 标题

    def test_intent_recognition_skill_content(self):
        """测试意图识别技能内容"""
        skills = create_all_orchestration_skills()
        intent_skill = next(s for s in skills if s.name == "intent_recognition")

        assert "检测意图" in intent_skill.system_prompt
        assert "规划意图" in intent_skill.system_prompt
        assert "pure_detection" in intent_skill.system_prompt
        assert "pure_planning" in intent_skill.system_prompt

    def test_scenario_switching_skill_content(self):
        """测试场景切换技能内容"""
        skills = create_all_orchestration_skills()
        scenario_skill = next(s for s in skills if s.name == "scenario_switching")

        assert "上下文连续性" in scenario_skill.system_prompt
        assert "检测 → 规划" in scenario_skill.system_prompt
        assert "规划 → 检测" in scenario_skill.system_prompt


class TestOrchestratorAgentV2:
    """测试 Orchestrator Agent V2"""

    def test_agent_exists(self):
        """测试 Agent 是否存在"""
        assert agent is not None

    def test_agent_tools(self):
        """测试 Agent 工具配置"""
        # 应该包含检测工具和 RAG 工具
        assert len(orchestrator_tools) >= 3

        tool_names = [tool.name for tool in orchestrator_tools]
        assert "pest_detection_tool" in tool_names
        assert "rice_detection_tool" in tool_names
        assert "cow_detection_tool" in tool_names

        # 检查 RAG 工具
        rag_tool_names = [
            "list_documents",
            "get_document_overview",
            "search_key_points",
            "search_knowledge",
            "get_chapter_content",
            "get_document_full",
        ]
        for rag_tool in rag_tool_names:
            assert rag_tool in tool_names

    def test_agent_skills_count(self):
        """测试 Agent 技能数量（检测3 + 规划1 + 编排2 = 6）"""
        expected_skills = 6
        assert len(all_skills) == expected_skills

    def test_agent_skills_categories(self):
        """测试 Agent 技能分类分布"""
        categories = {skill.category for skill in all_skills}
        assert "detection" in categories
        assert "planning" in categories
        assert "orchestration" in categories

    def test_agent_skill_names(self):
        """测试 Agent 技能名称"""
        skill_names = [skill.name for skill in all_skills]

        # 检测技能
        assert "pest_detection" in skill_names
        assert "rice_detection" in skill_names
        assert "cow_detection" in skill_names

        # 规划技能
        assert "consult_planning_knowledge" in skill_names

        # 编排技能
        assert "intent_recognition" in skill_names
        assert "scenario_switching" in skill_names

    def test_all_skills_enabled(self):
        """测试所有技能是否启用"""
        for skill in all_skills:
            assert skill.enabled is True

    def test_skill_tool_associations(self):
        """测试技能工具关联"""
        # 检测技能应该关联工具
        detection_skills = [s for s in all_skills if s.category == "detection"]
        for skill in detection_skills:
            assert len(skill.tools) > 0

        # 编排技能不应该关联工具（仅提供指导）
        orchestration_skills = [s for s in all_skills if s.category == "orchestration"]
        for skill in orchestration_skills:
            assert len(skill.tools) == 0


class TestSkillMiddlewareIntegration:
    """测试技能中间件集成"""

    def test_registered_skills(self):
        """测试技能是否正确注册到中间件"""
        from src.agents.middleware.skill_middleware import get_registered_skills

        registered = get_registered_skills()
        assert len(registered) >= 6  # 至少有 6 个技能

        # 检查关键技能是否注册
        assert "pest_detection" in registered
        assert "rice_detection" in registered
        assert "cow_detection" in registered
        assert "consult_planning_knowledge" in registered
        assert "intent_recognition" in registered
        assert "scenario_switching" in registered

    def test_load_skill_tool_exists(self):
        """测试 load_skill 工具是否存在"""
        from src.agents.middleware.skill_middleware import load_skill

        assert load_skill is not None
        assert load_skill.name == "load_skill"

    def test_load_skill_tool_functionality(self):
        """测试 load_skill 工具功能"""
        from src.agents.middleware.skill_middleware import load_skill

        # 测试加载存在的技能（调用工具的 func）
        result = load_skill.func("intent_recognition")
        assert "intent_recognition" in result
        assert "核心能力" in result

        # 测试加载不存在的技能
        result = load_skill.func("nonexistent_skill")
        assert "未找到" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

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

from src.agents.orchestrator_agent_v2 import agent, registry, orchestrator_tools
from src.agents.skills.base import Skill


class TestRegistrySkills:
    """测试从 YAML 配置加载的技能"""

    def test_skills_creation(self):
        """测试技能创建"""
        skills = registry.get_all_skills()
        assert len(skills) >= 6  # 至少有 6 个技能

        # 检查关键技能存在
        skill_names = [s.name for s in skills]
        assert "intent_recognition" in skill_names
        assert "scenario_switching" in skill_names

    def test_skill_types(self):
        """测试技能类型"""
        skills = registry.get_all_skills()
        for skill in skills:
            assert isinstance(skill, Skill)

    def test_skill_description_for_prompt(self):
        """测试技能描述生成"""
        skills = registry.get_all_skills()
        for skill in skills:
            description = skill.get_description_for_prompt()
            assert skill.name in description
            assert skill.description in description
            assert "**" in description  # Markdown 格式

    def test_skill_content(self):
        """测试技能内容"""
        skills = registry.get_all_skills()
        for skill in skills:
            content = skill.content
            # content 可能是中文，不包含英文名称，所以只检查长度
            assert len(content) > 0

    def test_intent_recognition_skill_content(self):
        """测试意图识别技能内容"""
        intent_skill = registry.get_skill("intent_recognition")
        assert intent_skill is not None

        # 根据 YAML 配置中的内容验证
        assert "约束条件" in intent_skill.content
        assert "示例" in intent_skill.content

    def test_scenario_switching_skill_content(self):
        """测试场景切换技能内容"""
        scenario_skill = registry.get_skill("scenario_switching")
        assert scenario_skill is not None

        # 根据 YAML 配置中的内容验证
        assert "约束条件" in scenario_skill.content
        assert "示例" in scenario_skill.content


class TestOrchestratorAgentV2:
    """测试 Orchestrator Agent V2"""

    def test_agent_exists(self):
        """测试 Agent 是否存在"""
        assert agent is not None

    def test_agent_tools(self):
        """测试 Agent 工具配置"""
        # 应该包含检测工具
        assert len(orchestrator_tools) >= 3

        tool_names = [tool.name for tool in orchestrator_tools]
        assert "pest_detection_tool" in tool_names
        assert "rice_detection_tool" in tool_names
        assert "cow_detection_tool" in tool_names
        assert "load_skill" in tool_names

    def test_agent_skills_count(self):
        """测试 Agent 技能数量"""
        # YAML 配置中有 6 个技能：pest, rice, cow, planning, pricing, marketing
        # 加上 inspection, disease_prediction, 和 2 个 orchestration
        skills = registry.get_all_skills()
        assert len(skills) >= 8  # 至少有 8 个技能

    def test_agent_skill_names(self):
        """测试 Agent 技能名称"""
        skill_names = [skill.name for skill in registry.get_all_skills()]

        # 检测技能
        assert "pest_detection" in skill_names
        assert "rice_detection" in skill_names
        assert "cow_detection" in skill_names

        # 规划技能
        assert "consult_planning_knowledge" in skill_names

        # 编排技能
        assert "intent_recognition" in skill_names
        assert "scenario_switching" in skill_names

    def test_skill_tool_associations(self):
        """测试技能工具关联（通过 tool_names 属性）"""
        # 检测技能应该有关联的工具名称
        detection_skills = [
            s for s in registry.get_all_skills()
            if s.name in ["pest_detection", "rice_detection", "cow_detection"]
        ]
        for skill in detection_skills:
            assert len(skill.tool_names) > 0, f"{skill.name} 应该有关联的工具"

        # 编排技能不应该关联工具（仅提供指导）
        orchestration_skills = [
            s for s in registry.get_all_skills()
            if s.name in ["intent_recognition", "scenario_switching"]
        ]
        for skill in orchestration_skills:
            assert len(skill.tool_names) == 0, f"{skill.name} 不应该关联工具"


class TestSkillRegistry:
    """测试技能注册中心"""

    def test_get_skill(self):
        """测试获取单个技能"""
        pest_skill = registry.get_skill("pest_detection")
        assert pest_skill is not None
        assert pest_skill.name == "pest_detection"
        assert "病虫害检测" in pest_skill.description

    def test_get_nonexistent_skill(self):
        """测试获取不存在的技能"""
        skill = registry.get_skill("nonexistent_skill")
        assert skill is None

    def test_list_skill_names(self):
        """测试列出技能名称"""
        names = registry.list_skill_names()
        assert len(names) >= 8
        assert "pest_detection" in names
        assert "rice_detection" in names

    def test_get_skill_descriptions(self):
        """测试获取技能描述"""
        descriptions = registry.get_skill_descriptions()
        assert "pest_detection" in descriptions
        assert "rice_detection" in descriptions
        assert "intent_recognition" in descriptions

    def test_load_content(self):
        """测试加载技能内容"""
        content = registry.load_content("pest_detection")
        assert "病虫害检测" in content
        assert len(content) > 0

    def test_load_nonexistent_content(self):
        """测试加载不存在的技能内容"""
        with pytest.raises(ValueError, match="未找到"):
            registry.load_content("nonexistent_skill")


class TestSkillMiddlewareIntegration:
    """测试技能中间件集成"""

    def test_registered_skills(self):
        """测试技能是否正确注册到注册中心"""
        registered = registry.list_skill_names()
        assert len(registered) >= 6  # 至少有 6 个技能

        # 检查关键技能是否注册
        assert "pest_detection" in registered
        assert "rice_detection" in registered
        assert "cow_detection" in registered
        assert "intent_recognition" in registered

    def test_load_skill_tool_exists(self):
        """测试 load_skill 工具是否存在"""
        from src.agents.tools.load_skill_tool import load_skill

        assert load_skill is not None
        assert load_skill.name == "load_skill"

    def test_load_skill_tool_functionality(self):
        """测试 load_skill 工具功能"""
        from src.agents.tools.load_skill_tool import load_skill

        # 测试加载存在的技能（调用工具的 invoke）
        result = load_skill.invoke({"skill_name": "pest_detection"})
        assert "pest_detection" in result
        assert "病虫害检测" in result

        # 测试加载不存在的技能
        result = load_skill.invoke({"skill_name": "nonexistent_skill"})
        assert "未找到" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

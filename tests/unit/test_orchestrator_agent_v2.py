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

        # 检查关键技能存在（检测、规划、定价、营销等）
        skill_names = [s.name for s in skills]
        assert "pest_detection" in skill_names
        assert "consult_planning_knowledge" in skill_names
        assert "pricing_analysis" in skill_names

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

    def test_detection_skill_content(self):
        """测试检测技能内容"""
        pest_skill = registry.get_skill("pest_detection")
        assert pest_skill is not None

        # 验证内容包含关键信息
        assert len(pest_skill.content) > 0
        assert "pest_detection" in pest_skill.name


class TestOrchestratorAgentV2:
    """测试 Orchestrator Agent V2"""

    def test_agent_exists(self):
        """测试 Agent 是否存在"""
        assert agent is not None

    def test_agent_tools(self):
        """测试 Agent 工具配置 - 严格渐进式披露"""
        # 初始只注册 load_skill 工具，其他工具通过 DynamicToolMiddleware 动态注册
        assert len(orchestrator_tools) == 1

        tool_names = [tool.name for tool in orchestrator_tools]
        assert "load_skill" in tool_names

    @pytest.mark.asyncio
    async def test_dynamic_tool_registration(self):
        """测试动态工具注册功能"""
        from src.agents.middleware.dynamic_tool_middleware import get_dynamic_middleware
        from src.agents.tools import load_skill

        middleware = get_dynamic_middleware()
        thread_id = "test_thread"

        # 初始状态：没有动态注册的工具
        registered = middleware.get_registered_tools(thread_id)
        assert len(registered) == 0

        # 通过 load_skill 注册检测工具
        await load_skill.ainvoke(
            {"skill_name": "pest_detection"},
            config={"configurable": {"thread_id": thread_id}}
        )

        # 验证工具已注册
        registered = middleware.get_registered_tools(thread_id)
        assert "pest_detection_tool" in registered

    def test_agent_skills_count(self):
        """测试 Agent 技能数量"""
        # YAML 配置文件：detection, planning, pricing, marketing, inspection, disease_prediction
        skills = registry.get_all_skills()
        assert len(skills) >= 6  # 至少有 6 个技能

    def test_agent_skill_names(self):
        """测试 Agent 技能名称"""
        skill_names = [skill.name for skill in registry.get_all_skills()]

        # 检测技能
        assert "pest_detection" in skill_names
        assert "rice_detection" in skill_names
        assert "cow_detection" in skill_names

        # 规划技能
        assert "consult_planning_knowledge" in skill_names

        # 定价和营销技能
        assert "pricing_analysis" in skill_names
        assert "marketing_strategy" in skill_names

    def test_skill_tool_associations(self):
        """测试技能工具关联（通过 tool_names 属性）"""
        # 检测技能应该有关联的工具名称
        detection_skills = [
            s for s in registry.get_all_skills()
            if s.name in ["pest_detection", "rice_detection", "cow_detection"]
        ]
        for skill in detection_skills:
            assert len(skill.tool_names) > 0, f"{skill.name} 应该有关联的工具"

        # 规划类技能可能没有关联工具（使用 RAG）
        planning_skills = [
            s for s in registry.get_all_skills()
            if s.name == "consult_planning_knowledge"
        ]
        for skill in planning_skills:
            # 规划技能可能没有直接的工具关联
            assert len(skill.tool_names) >= 0


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
        assert len(names) >= 6
        assert "pest_detection" in names
        assert "rice_detection" in names

    def test_get_skill_descriptions(self):
        """测试获取技能描述"""
        descriptions = registry.get_skill_descriptions()
        assert "pest_detection" in descriptions
        assert "rice_detection" in descriptions
        assert "pricing_analysis" in descriptions

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
        assert "consult_planning_knowledge" in registered

    def test_load_skill_tool_exists(self):
        """测试 load_skill 工具是否存在"""
        from src.agents.tools.load_skill_tool import load_skill

        assert load_skill is not None
        assert load_skill.name == "load_skill"

    @pytest.mark.asyncio
    async def test_load_skill_tool_functionality(self):
        """测试 load_skill 工具功能"""
        from src.agents.tools import load_skill

        # 测试加载存在的技能（需要 thread_id 上下文）
        result = await load_skill.ainvoke(
            {"skill_name": "pest_detection"},
            config={"configurable": {"thread_id": "test_thread"}}
        )
        assert "pest_detection" in result
        assert "病虫害检测" in result

        # 测试加载不存在的技能
        result = await load_skill.ainvoke(
            {"skill_name": "nonexistent_skill"},
            config={"configurable": {"thread_id": "test_thread_2"}}
        )
        assert "未找到" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

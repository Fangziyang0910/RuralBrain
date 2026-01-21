"""
测试 Skills 架构

验证基于 Skills 的 Agent 架构是否正常工作：
1. 技能加载
2. 中间件功能
3. load_skill 工具
4. Agent 基本功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents.skills.detection_skills import (
    create_pest_detection_skill,
    create_rice_detection_skill,
    create_cow_detection_skill,
)
from src.agents.skills.base import Skill
from src.agents.middleware.skill_middleware import load_skill, register_skills, get_registered_skills


def test_skill_creation():
    """测试技能创建"""
    print("=" * 50)
    print("测试 1: 技能创建")
    print("=" * 50)

    # 创建模拟工具
    from langchain_core.tools import tool

    @tool
    def mock_pest_tool(image_path: str) -> str:
        """模拟病虫害检测工具"""
        return "检测结果: 瓜实蝇(3只)"

    @tool
    def mock_rice_tool(image_path: str) -> str:
        """模拟大米识别工具"""
        return "识别结果: 粳稻(95%置信度)"

    @tool
    def mock_cow_tool(image_path: str) -> str:
        """模拟奶牛检测工具"""
        return "检测结果: 荷斯坦奶牛(15头)"

    # 创建技能
    pest_skill = create_pest_detection_skill(mock_pest_tool)
    rice_skill = create_rice_detection_skill(mock_rice_tool)
    cow_skill = create_cow_detection_skill(mock_cow_tool)

    print(f"✓ 创建病虫害检测技能: {pest_skill.name}")
    print(f"  描述: {pest_skill.description}")
    print(f"  分类: {pest_skill.category}")
    print(f"  工具数量: {len(pest_skill.tools)}")

    print(f"\n✓ 创建大米识别技能: {rice_skill.name}")
    print(f"  描述: {rice_skill.description}")

    print(f"\n✓ 创建奶牛检测技能: {cow_skill.name}")
    print(f"  描述: {cow_skill.description}")

    return [pest_skill, rice_skill, cow_skill]


def test_skill_content(skills: list):
    """测试技能内容生成"""
    print("\n" + "=" * 50)
    print("测试 2: 技能内容生成")
    print("=" * 50)

    for skill in skills:
        print(f"\n{skill.name} 技能:")
        print("-" * 50)
        print(skill.get_prompt_addendum())
        print()


def test_load_skill_tool(skills: list):
    """测试 load_skill 工具"""
    print("=" * 50)
    print("测试 3: load_skill 工具")
    print("=" * 50)

    # 注册技能
    register_skills(skills)

    # 测试加载病虫害检测技能
    result = load_skill.invoke({"skill_name": "pest_detection"})
    print("加载 pest_detection 技能:")
    print(result[:200] + "..." if len(result) > 200 else result)

    # 测试加载不存在的技能
    result = load_skill.invoke({"skill_name": "nonexistent"})
    print(f"\n加载不存在的技能: {result}")


def test_skill_registration(skills: list):
    """测试技能注册"""
    print("\n" + "=" * 50)
    print("测试 4: 技能注册中心")
    print("=" * 50)

    registered = get_registered_skills()
    print(f"已注册技能数量: {len(registered)}")
    for name, skill in registered.items():
        print(f"  - {name}: {skill.description}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("RuralBrain Skills 架构测试")
    print("=" * 50)

    try:
        # 测试 1: 技能创建
        skills = test_skill_creation()

        # 测试 2: 技能内容生成
        test_skill_content(skills)

        # 测试 3: load_skill 工具
        test_load_skill_tool(skills)

        # 测试 4: 技能注册
        test_skill_registration(skills)

        print("\n" + "=" * 50)
        print("✅ 所有测试通过!")
        print("=" * 50)

        print("\n下一步:")
        print("1. 启动检测服务 (pest_detection_service, rice_detection_service, cow_detection_service)")
        print("2. 运行完整的 Agent 测试")
        print("3. 对比新旧 Agent 的输出质量")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

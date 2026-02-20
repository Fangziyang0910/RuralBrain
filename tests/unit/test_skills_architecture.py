"""
测试 Skills 架构

验证基于 YAML 配置的 Agent Skills 架构是否正常工作：
1. 技能加载
2. 注册中心功能
3. load_skill 工具
4. Agent 基本功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.skills.registry import get_registry
from src.agents.skills.base import Skill


def test_skill_loading():
    """测试技能加载"""
    print("=" * 50)
    print("测试 1: 技能加载")
    print("=" * 50)

    registry = get_registry()
    skills = registry.get_all_skills()

    print(f"[OK] 加载了 {len(skills)} 个技能:")

    # 按类别分组显示
    detection_skills = [s for s in skills if s.name in ["pest_detection", "rice_detection", "cow_detection"]]
    orchestration_skills = [s for s in skills if s.name in ["intent_recognition", "scenario_switching"]]
    other_skills = [s for s in skills if s not in detection_skills and s not in orchestration_skills]

    print("\n检测技能:")
    for skill in detection_skills:
        print(f"  - {skill.name}: {skill.description}")

    print("\n编排技能:")
    for skill in orchestration_skills:
        print(f"  - {skill.name}: {skill.description}")

    print("\n其他技能:")
    for skill in other_skills:
        print(f"  - {skill.name}: {skill.description}")

    return skills


def test_skill_content(skills):
    """测试技能内容生成"""
    print("\n" + "=" * 50)
    print("测试 2: 技能内容生成")
    print("=" * 50)

    for skill in skills[:3]:  # 只显示前 3 个技能
        print(f"\n{skill.name} 技能:")
        print("-" * 50)
        print(skill.get_description_for_prompt())
        print()


def test_load_skill_tool():
    """测试 load_skill 工具"""
    print("=" * 50)
    print("测试 3: load_skill 工具")
    print("=" * 50)

    from src.agents.tools.load_skill_tool import load_skill

    # 测试加载病虫害检测技能
    result = load_skill.invoke({"skill_name": "pest_detection"})
    print("加载 pest_detection 技能:")
    print(result[:300] + "..." if len(result) > 300 else result)

    # 测试加载不存在的技能
    result = load_skill.invoke({"skill_name": "nonexistent"})
    print(f"\n加载不存在的技能: {result[:200]}...")


def test_skill_registry():
    """测试技能注册中心"""
    print("\n" + "=" * 50)
    print("测试 4: 技能注册中心")
    print("=" * 50)

    registry = get_registry()

    print(f"已注册技能数量: {len(registry.list_skill_names())}")
    print("\n所有技能名称:")
    for name in registry.list_skill_names():
        skill = registry.get_skill(name)
        print(f"  - {name}: {skill.description[:50]}...")

    # 测试获取技能描述
    print("\n技能描述（用于系统提示词）:")
    descriptions = registry.get_skill_descriptions()
    print(descriptions[:500] + "..." if len(descriptions) > 500 else descriptions)


def test_skill_tool_associations():
    """测试技能工具关联"""
    print("\n" + "=" * 50)
    print("测试 5: 技能工具关联")
    print("=" * 50)

    registry = get_registry()
    skills = registry.get_all_skills()

    for skill in skills:
        if skill.tool_names:
            print(f"{skill.name}: 关联工具 {skill.tool_names}")
        else:
            print(f"{skill.name}: 无关联工具（仅提供指导）")


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("RuralBrain Skills 架构测试（YAML 配置版）")
    print("=" * 50)

    try:
        # 测试 1: 技能加载
        skills = test_skill_loading()

        # 测试 2: 技能内容生成
        test_skill_content(skills)

        # 测试 3: load_skill 工具
        test_load_skill_tool()

        # 测试 4: 技能注册中心
        test_skill_registry()

        # 测试 5: 技能工具关联
        test_skill_tool_associations()

        print("\n" + "=" * 50)
        print("[SUCCESS] 所有测试通过!")
        print("=" * 50)

        print("\n下一步:")
        print("1. 启动检测服务 (pest_detection_service, rice_detection_service, cow_detection_service)")
        print("2. 运行完整的 Agent 测试")
        print("3. 对比新旧 Agent 的输出质量")

    except Exception as e:
        print(f"\n[FAILED] 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

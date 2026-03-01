"""
测试工具生命周期管理 (ToolLifecycle)

验证 TTL 系统的核心功能：
1. TTLConfig 配置模型
2. ToolLifecycle 生命周期追踪
3. 过期检测、续期、衰减等核心方法
4. 钉住工具的特殊行为
"""
import sys
from pathlib import Path

# 设置 UTF-8 编码输出（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.middleware.tool_lifecycle import TTLConfig, ToolLifecycle
from src.config import DEFAULT_TOOL_TTL, DEFAULT_TOOL_EXTENSION


def test_ttl_config_defaults():
    """测试 1: TTLConfig 默认值"""
    print("=" * 60)
    print("测试 1: TTLConfig 默认值")
    print("=" * 60)

    config = TTLConfig()

    assert config.base_ttl == DEFAULT_TOOL_TTL, \
        f"默认 base_ttl 应为 {DEFAULT_TOOL_TTL}，实际 {config.base_ttl}"
    print(f"  ✓ 默认 base_ttl = {DEFAULT_TOOL_TTL}")

    assert config.extension == DEFAULT_TOOL_EXTENSION, \
        f"默认 extension 应为 {DEFAULT_TOOL_EXTENSION}，实际 {config.extension}"
    print(f"  ✓ 默认 extension = {DEFAULT_TOOL_EXTENSION}")

    assert config.pinned is False, "默认 pinned 应为 False"
    print(f"  ✓ 默认 pinned = False")

    return True


def test_ttl_config_custom():
    """测试 2: TTLConfig 自定义值"""
    print("\n" + "=" * 60)
    print("测试 2: TTLConfig 自定义值")
    print("=" * 60)

    config = TTLConfig(base_ttl=5, extension=2, pinned=True)

    assert config.base_ttl == 5, f"base_ttl 应为 5，实际 {config.base_ttl}"
    print(f"  ✓ 自定义 base_ttl = 5")

    assert config.extension == 2, f"extension 应为 2，实际 {config.extension}"
    print(f"  ✓ 自定义 extension = 2")

    assert config.pinned is True, "pinned 应为 True"
    print(f"  ✓ 自定义 pinned = True")

    return True


def test_tool_lifecycle_creation():
    """测试 3: ToolLifecycle 创建"""
    print("\n" + "=" * 60)
    print("测试 3: ToolLifecycle 创建")
    print("=" * 60)

    lifecycle = ToolLifecycle(
        tool_name="pest_detection_tool",
        skill_name="pest_detection",
        current_ttl=3,
        base_ttl=3,
        extension=2,
        pinned=False,
        registration_round=0,
        last_used_round=None
    )

    assert lifecycle.tool_name == "pest_detection_tool"
    print(f"  ✓ 工具名称: {lifecycle.tool_name}")

    assert lifecycle.current_ttl == 3
    print(f"  ✓ 当前 TTL: {lifecycle.current_ttl}")

    assert lifecycle.registration_round == 0
    print(f"  ✓ 注册轮次: {lifecycle.registration_round}")

    assert lifecycle.last_used_round is None
    print(f"  ✓ 最后使用轮次: None")

    return True


def test_is_expired_normal_tool():
    """测试 4: 普通工具过期检测"""
    print("\n" + "=" * 60)
    print("测试 4: 普通工具过期检测")
    print("=" * 60)

    # 未过期
    lifecycle = ToolLifecycle(
        tool_name="test_tool",
        skill_name="test_skill",
        current_ttl=2,
        base_ttl=3,
        extension=1,
        pinned=False,
        registration_round=0
    )

    assert not lifecycle.is_expired(), "TTL=2 时不应过期"
    print(f"  ✓ TTL=2 时未过期")

    # 即将过期
    lifecycle.current_ttl = 1
    assert not lifecycle.is_expired(), "TTL=1 时不应过期"
    print(f"  ✓ TTL=1 时未过期")

    # 已过期
    lifecycle.current_ttl = 0
    assert lifecycle.is_expired(), "TTL=0 时应过期"
    print(f"  ✓ TTL=0 时已过期")

    return True


def test_is_expired_pinned_tool():
    """测试 5: 钉住工具永不过期"""
    print("\n" + "=" * 60)
    print("测试 5: 钉住工具永不过期")
    print("=" * 60)

    lifecycle = ToolLifecycle(
        tool_name="pinned_tool",
        skill_name="pinned_skill",
        current_ttl=0,
        base_ttl=3,
        extension=1,
        pinned=True,  # 钉住
        registration_round=0
    )

    # 即使 TTL=0，钉住工具也不过期
    assert not lifecycle.is_expired(), "钉住工具永不过期"
    print(f"  ✓ 钉住工具 (TTL=0) 未过期")

    # 负数也不过期
    lifecycle.current_ttl = -1
    assert not lifecycle.is_expired(), "钉住工具 TTL 为负数时也不过期"
    print(f"  ✓ 钉住工具 (TTL=-1) 未过期")

    return True


def test_renew_normal_tool():
    """测试 6: 普通工具续期"""
    print("\n" + "=" * 60)
    print("测试 6: 普通工具续期")
    print("=" * 60)

    lifecycle = ToolLifecycle(
        tool_name="test_tool",
        skill_name="test_skill",
        current_ttl=1,
        base_ttl=3,
        extension=2,
        pinned=False,
        registration_round=0
    )

    # 续期后 TTL = base_ttl + extension
    new_ttl = lifecycle.renew()
    expected_ttl = 3 + 2  # base_ttl + extension

    assert new_ttl == expected_ttl, f"续期后 TTL 应为 {expected_ttl}，实际 {new_ttl}"
    assert lifecycle.current_ttl == expected_ttl
    print(f"  ✓ 续期后 TTL = {expected_ttl} (base_ttl=3, extension=2)")

    return True


def test_renew_pinned_tool():
    """测试 7: 钉住工具续期（TTL 不变）"""
    print("\n" + "=" * 60)
    print("测试 7: 钉住工具续期（TTL 不变）")
    print("=" * 60)

    original_ttl = 999
    lifecycle = ToolLifecycle(
        tool_name="pinned_tool",
        skill_name="pinned_skill",
        current_ttl=original_ttl,
        base_ttl=3,
        extension=2,
        pinned=True,
        registration_round=0
    )

    # 钉住工具续期后 TTL 不变
    new_ttl = lifecycle.renew()

    assert new_ttl == original_ttl, f"钉住工具续期后 TTL 应保持 {original_ttl}，实际 {new_ttl}"
    assert lifecycle.current_ttl == original_ttl
    print(f"  ✓ 钉住工具续期后 TTL 保持不变 = {original_ttl}")

    return True


def test_decrement_normal_tool():
    """测试 8: 普通工具 TTL 衰减"""
    print("\n" + "=" * 60)
    print("测试 8: 普通工具 TTL 衰减")
    print("=" * 60)

    lifecycle = ToolLifecycle(
        tool_name="test_tool",
        skill_name="test_skill",
        current_ttl=3,
        base_ttl=3,
        extension=1,
        pinned=False,
        registration_round=0
    )

    # 第一次衰减
    ttl = lifecycle.decrement()
    assert ttl == 2, f"第一次衰减后 TTL 应为 2，实际 {ttl}"
    print(f"  ✓ 第一次衰减: TTL 3 -> 2")

    # 第二次衰减
    ttl = lifecycle.decrement()
    assert ttl == 1, f"第二次衰减后 TTL 应为 1，实际 {ttl}"
    print(f"  ✓ 第二次衰减: TTL 2 -> 1")

    # 第三次衰减
    ttl = lifecycle.decrement()
    assert ttl == 0, f"第三次衰减后 TTL 应为 0，实际 {ttl}"
    print(f"  ✓ 第三次衰减: TTL 1 -> 0")

    # 继续衰减不会变为负数
    ttl = lifecycle.decrement()
    assert ttl == 0, f"TTL 达到 0 后不应变为负数，实际 {ttl}"
    print(f"  ✓ TTL 达到 0 后不再减少")

    return True


def test_decrement_pinned_tool():
    """测试 9: 钉住工具 TTL 不衰减"""
    print("\n" + "=" * 60)
    print("测试 9: 钉住工具 TTL 不衰减")
    print("=" * 60)

    original_ttl = 100
    lifecycle = ToolLifecycle(
        tool_name="pinned_tool",
        skill_name="pinned_skill",
        current_ttl=original_ttl,
        base_ttl=3,
        extension=1,
        pinned=True,
        registration_round=0
    )

    # 钉住工具衰减后 TTL 不变
    ttl = lifecycle.decrement()
    assert ttl == original_ttl, f"钉住工具衰减后 TTL 应保持 {original_ttl}，实际 {ttl}"
    print(f"  ✓ 钉住工具衰减后 TTL 保持不变 = {original_ttl}")

    return True


def test_mark_used():
    """测试 10: 标记工具使用"""
    print("\n" + "=" * 60)
    print("测试 10: 标记工具使用")
    print("=" * 60)

    lifecycle = ToolLifecycle(
        tool_name="test_tool",
        skill_name="test_skill",
        current_ttl=3,
        base_ttl=3,
        extension=1,
        pinned=False,
        registration_round=0,
        last_used_round=None
    )

    assert lifecycle.last_used_round is None
    print(f"  ✓ 初始 last_used_round = None")

    lifecycle.mark_used(5)
    assert lifecycle.last_used_round == 5
    print(f"  ✓ 标记使用后 last_used_round = 5")

    lifecycle.mark_used(10)
    assert lifecycle.last_used_round == 10
    print(f"  ✓ 更新标记后 last_used_round = 10")

    return True


def test_get_status():
    """测试 11: 获取工具状态"""
    print("\n" + "=" * 60)
    print("测试 11: 获取工具状态")
    print("=" * 60)

    lifecycle = ToolLifecycle(
        tool_name="pest_detection_tool",
        skill_name="pest_detection",
        current_ttl=2,
        base_ttl=3,
        extension=1,
        pinned=False,
        registration_round=1,
        last_used_round=3
    )

    status = lifecycle.get_status()

    assert status["tool_name"] == "pest_detection_tool"
    assert status["skill_name"] == "pest_detection"
    assert status["current_ttl"] == 2
    assert status["base_ttl"] == 3
    assert status["extension"] == 1
    assert status["pinned"] is False
    assert status["registration_round"] == 1
    assert status["last_used_round"] == 3
    assert status["expired"] is False  # TTL=2 未过期

    print(f"  ✓ get_status() 返回完整的状态信息")
    print(f"    {status}")

    return True


def test_full_lifecycle_workflow():
    """测试 12: 完整生命周期工作流"""
    print("\n" + "=" * 60)
    print("测试 12: 完整生命周期工作流")
    print("=" * 60)

    # 创建工具生命周期 (base_ttl=2, extension=1)
    lifecycle = ToolLifecycle(
        tool_name="test_tool",
        skill_name="test_skill",
        current_ttl=2,
        base_ttl=2,
        extension=1,
        pinned=False,
        registration_round=0
    )

    print(f"  [注册] TTL = {lifecycle.current_ttl}")

    # 第 1 轮：衰减
    lifecycle.decrement()
    print(f"  [第1轮衰减] TTL = {lifecycle.current_ttl}")
    assert not lifecycle.is_expired()

    # 第 2 轮：衰减，工具过期
    lifecycle.decrement()
    print(f"  [第2轮衰减] TTL = {lifecycle.current_ttl}")
    assert lifecycle.is_expired()
    print(f"  ✓ 工具已过期")

    # 续期
    lifecycle.renew()
    new_ttl = lifecycle.current_ttl
    print(f"  [续期] TTL = {new_ttl}")
    assert new_ttl == 3  # base_ttl + extension
    assert not lifecycle.is_expired()
    print(f"  ✓ 续期后 TTL = {new_ttl}，工具恢复活跃")

    # 标记使用
    lifecycle.mark_used(3)
    assert lifecycle.last_used_round == 3
    print(f"  ✓ 标记在第 3 轮使用")

    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("ToolLifecycle 单元测试")
    print("=" * 60)

    tests = [
        ("TTLConfig 默认值", test_ttl_config_defaults),
        ("TTLConfig 自定义值", test_ttl_config_custom),
        ("ToolLifecycle 创建", test_tool_lifecycle_creation),
        ("普通工具过期检测", test_is_expired_normal_tool),
        ("钉住工具永不过期", test_is_expired_pinned_tool),
        ("普通工具续期", test_renew_normal_tool),
        ("钉住工具续期", test_renew_pinned_tool),
        ("普通工具 TTL 衰减", test_decrement_normal_tool),
        ("钉住工具 TTL 不衰减", test_decrement_pinned_tool),
        ("标记工具使用", test_mark_used),
        ("获取工具状态", test_get_status),
        ("完整生命周期工作流", test_full_lifecycle_workflow),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n  ✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 摘要
    print("\n" + "=" * 60)
    print("测试摘要")
    print("=" * 60)

    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {status}: {name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)
    print(f"\n  总计: {passed_count}/{total} 通过")

    if all(p for _, p in results):
        print("\n  ✅ 所有测试通过!")
        return 0
    else:
        print("\n  ❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit(main())

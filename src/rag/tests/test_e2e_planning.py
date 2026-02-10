"""
Planning Agent 端到端集成测试
测试场景：用户提出乡村发展规划问题，验证智能体能否使用阶段1+阶段2工具给出好的回答

测试策略：
1. 快速模式问题：简单明确的问题，应该使用摘要工具快速回答
2. 深度模式问题：复杂的规划决策问题，应该深入阅读文档
3. 混合模式问题：需要筛选和对比的问题

评估标准：
- 工具使用合理性：是否选择了合适的工具组合
- 回答质量：信息是否准确、结构是否清晰、是否有决策建议
- 效率性：是否能快速回答简单问题，深度回答复杂问题
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.agents.planning_agent import agent
import uuid


def test_scenario(name: str, user_input: str, expected_mode: str):
    """
    测试单个场景

    Args:
        name: 测试场景名称
        user_input: 用户输入
        expected_mode: 期望的工作模式（快速/深度）
    """
    print("\n" + "="*80)
    print(f"测试场景：{name}")
    print("="*80)
    print(f"👤 用户问题：{user_input}")
    print(f"🎯 期望模式：{expected_mode}模式")

    # 创建新的对话线程
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("🤖 Agent 正在思考...")

    # 记录工具调用
    tools_called = []

    # Stream 模式
    events = agent.stream(
        {"messages": [("user", user_input)]},
        config,
        stream_mode="values"
    )

    final_response = None
    for event in events:
        if "messages" in event:
            for msg in event["messages"]:
                # 记录工具调用
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get('name', 'unknown')
                        tools_called.append(tool_name)
                        print(f"   🔧 调用工具：{tool_name}")

                # 获取最终回复
                if msg.type == "ai" and msg.content:
                    final_response = msg.content

    print("\n📊 工具调用统计：")
    if tools_called:
        for tool in tools_called:
            print(f"   - {tool}")
    else:
        print("   （未调用工具）")

    print(f"\n🎓 Agent 回答：\n{final_response}")

    # 分析工具使用模式
    mode_analysis = analyze_mode(tools_called)
    print(f"\n📈 实际模式分析：{mode_analysis['mode']}模式")

    # 评估结果
    evaluation = {
        "scenario": name,
        "expected_mode": expected_mode,
        "actual_mode": mode_analysis['mode'],
        "tools_called": tools_called,
        "response_length": len(final_response) if final_response else 0,
        "passed": mode_analysis['mode'] == expected_mode
    }

    return evaluation


def analyze_mode(tools_called):
    """
    分析工具使用模式

    Returns:
        dict: 包含模式和分析结果
    """
    if not tools_called:
        return {"mode": "无工具", "reasoning": "没有调用任何工具"}

    # 快速模式工具
    fast_mode_tools = {
        "get_executive_summary",
        "list_chapter_summaries",
        "get_chapter_summary",
        "search_key_points",
    }

    # 深度模式工具
    deep_mode_tools = {
        "get_full_document",
        "get_chapter_by_header",
        "search_rural_planning_knowledge",
    }

    fast_count = sum(1 for t in tools_called if t in fast_mode_tools)
    deep_count = sum(1 for t in tools_called if t in deep_mode_tools)

    if fast_count > 0 and deep_count == 0:
        return {
            "mode": "快速",
            "reasoning": f"使用了 {fast_count} 个快速模式工具，未使用深度模式工具"
        }
    elif deep_count > 0 and fast_count == 0:
        return {
            "mode": "深度",
            "reasoning": f"使用了 {deep_count} 个深度模式工具，未使用快速模式工具"
        }
    elif fast_count > 0 and deep_count > 0:
        # 判断主导模式
        if fast_count > deep_count:
            return {
                "mode": "混合（偏快速）",
                "reasoning": f"使用了 {fast_count} 个快速工具和 {deep_count} 个深度工具"
            }
        else:
            return {
                "mode": "混合（偏深度）",
                "reasoning": f"使用了 {deep_count} 个深度工具和 {fast_count} 个快速工具"
            }
    else:
        return {
            "mode": "其他",
            "reasoning": "未识别到主要模式工具"
        }


def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("Planning Agent 端到端集成测试")
    print("测试目标：验证智能体能否使用阶段1+阶段2工具有效回答规划问题")
    print("="*80)

    # 定义测试场景
    scenarios = [
        {
            "name": "场景1：简单事实查询（快速模式）",
            "input": "长宁镇的旅游发展目标是什么？",
            "expected_mode": "快速"
        },
        {
            "name": "场景2：关键指标查询（快速模式）",
            "input": "罗浮山片区预计投资多少？",
            "expected_mode": "快速"
        },
        {
            "name": "场景3：复杂规划决策（深度模式）",
            "input": "帮我制定长宁镇乡村旅游发展策略",
            "expected_mode": "深度"
        },
        {
            "name": "场景4：多文档对比（快速模式）",
            "input": "有哪些主要的发展目标和重点项目？",
            "expected_mode": "快速"
        },
    ]

    results = []

    # 运行测试场景
    for scenario in scenarios:
        try:
            result = test_scenario(
                scenario["name"],
                scenario["input"],
                scenario["expected_mode"]
            )
            results.append(result)

            # 短暂暂停，避免 API 限流
            import time
            time.sleep(2)

        except Exception as e:
            print(f"\n❌ 测试失败：{str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                "scenario": scenario["name"],
                "error": str(e),
                "passed": False
            })

    # 汇总结果
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)

    passed = 0
    failed = 0

    for i, result in enumerate(results, 1):
        if "error" in result:
            status = "❌ 失败"
            failed += 1
            print(f"\n{i}. {result['scenario']}")
            print(f"   状态：{status}")
            print(f"   错误：{result['error']}")
        else:
            if result['passed']:
                status = "✅ 通过"
                passed += 1
            else:
                status = "⚠️  模式不匹配"
                failed += 1

            print(f"\n{i}. {result['scenario']}")
            print(f"   期望模式：{result['expected_mode']}模式")
            print(f"   实际模式：{result['actual_mode']}模式")
            print(f"   状态：{status}")
            print(f"   工具调用：{', '.join(result['tools_called']) if result['tools_called'] else '无'}")
            print(f"   回答长度：{result['response_length']} 字符")

    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    print(f"总场景数：{len(results)}")
    print(f"通过：{passed}")
    print(f"失败/警告：{failed}")
    print(f"通过率：{passed/len(results)*100:.1f}%")

    if passed == len(results):
        print("\n🎉 所有测试通过！Planning Agent 能够正确使用阶段1+阶段2工具。")
    else:
        print("\n⚠️  部分测试未通过，建议检查 Agent 的工具选择逻辑。")

    # 提供优化建议
    print("\n💡 优化建议：")
    print("1. 如果简单问题也使用深度模式，可能需要调整提示词强调效率")
    print("2. 如果复杂问题只用快速模式，可能需要强调深度分析的必要性")
    print("3. 观察工具调用的顺序，确保符合工作流程")


if __name__ == "__main__":
    main()

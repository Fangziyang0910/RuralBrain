"""
规划咨询服务完整集成测试
按照之前测试报告的标准，测试9个问题并收集性能指标
"""
import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# 导入测试工具模块
from test_utils import (
    save_results,
    get_latest_results,
    generate_html_report,
)


# 测试问题列表（与之前测试报告一致）
TEST_QUESTIONS = [
    # 基础查询（自动模式）
    {
        "id": "Q1",
        "question": "罗浮山的文化底蕴是什么？",
        "mode": "auto",
        "category": "基础查询"
    },
    {
        "id": "Q2",
        "question": "长宁镇的规划范围有多大？",
        "mode": "auto",
        "category": "基础查询"
    },
    {
        "id": "Q3",
        "question": "长宁镇的GDP是多少？",
        "mode": "auto",
        "category": "基础查询"
    },
    # 快速浏览模式
    {
        "id": "Q4",
        "question": "长宁镇如何实现山镇融合高质量发展？",
        "mode": "fast",
        "category": "快速浏览"
    },
    {
        "id": "Q5",
        "question": "罗浮山-长宁镇的'2315'产业体系是什么？",
        "mode": "fast",
        "category": "快速浏览"
    },
    # 深度分析模式
    {
        "id": "Q6",
        "question": "长宁镇的'双核三轴，一带三谷'空间格局具体指什么？",
        "mode": "deep",
        "category": "深度分析"
    },
    {
        "id": "Q7",
        "question": "玄碧湖旅游度假区的规划内容是什么？",
        "mode": "deep",
        "category": "深度分析"
    },
    # 综合问题（自动模式）
    {
        "id": "Q8",
        "question": "长宁镇在环南昆山-罗浮山引领区中的定位是什么？",
        "mode": "auto",
        "category": "综合问题"
    },
    {
        "id": "Q9",
        "question": "长宁镇的五大行动计划是什么？",
        "mode": "auto",
        "category": "综合问题"
    },
]


async def test_single_question(
    session: aiohttp.ClientSession,
    question_data: Dict[str, Any],
    base_url: str = "http://localhost:8003/api/v1"
) -> Dict[str, Any]:
    """
    测试单个问题并收集性能指标

    Args:
        session: aiohttp会话
        question_data: 问题数据
        base_url: API基础URL

    Returns:
        包含性能指标的测试结果
    """
    question_id = question_data["id"]
    question = question_data["question"]
    mode = question_data["mode"]
    category = question_data["category"]

    print(f"\n{'='*80}")
    print(f"{question_id}: {question}")
    print(f"分类: {category} | 模式: {mode}")
    print(f"{'='*80}")

    url = f"{base_url}/chat/planning"
    payload = {
        "message": question,
        "mode": mode
    }

    # 性能指标
    start_time = time.time()
    first_response_time = None
    total_chunks = 0
    full_response = ""
    tools_called = []
    sources_count = 0

    try:
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                return {
                    "id": question_id,
                    "question": question,
                    "mode": mode,
                    "category": category,
                    "error": f"HTTP {response.status}: {error_text}",
                    "success": False
                }

            # 读取SSE流
            async for line in response.content:
                line = line.decode('utf-8').strip()

                if not line or not line.startswith('data: '):
                    continue

                # 记录首次响应时间
                if first_response_time is None:
                    first_response_time = time.time() - start_time

                # 解析JSON数据
                try:
                    json_str = line[6:]  # 去掉 "data: " 前缀
                    data = json.loads(json_str)
                    event_type = data.get("type")

                    if event_type == "content":
                        content = data.get("content", "")
                        full_response += content
                        total_chunks += 1

                    elif event_type == "tool":
                        tool_name = data.get("tool_name", "")
                        if tool_name and tool_name not in tools_called:
                            tools_called.append(tool_name)
                            print(f"  🔧 调用工具: {tool_name}")

                    elif event_type == "sources":
                        sources = data.get("sources", [])
                        sources_count = len(sources)
                        print(f"  📚 知识库引用: {sources_count} 条")

                    elif event_type == "end":
                        break

                except json.JSONDecodeError as e:
                    print(f"  ⚠️  JSON解析错误: {e}")
                    continue

    except Exception as e:
        return {
            "id": question_id,
            "question": question,
            "mode": mode,
            "category": category,
            "error": str(e),
            "success": False
        }

    # 计算总耗时
    total_time = time.time() - start_time

    # 输出结果
    print(f"\n📊 性能指标:")
    print(f"  • 首字响应: {first_response_time:.2f}s" if first_response_time else "  • 首字响应: N/A")
    print(f"  • 总耗时: {total_time:.2f}s")
    print(f"  • 总块数: {total_chunks}")
    print(f"  • 回答长度: {len(full_response)} 字符")
    print(f"  • 工具调用: {len(tools_called)} 次 ({', '.join(tools_called) if tools_called else '无'})")
    print(f"  • 知识库引用: {sources_count} 条")

    # 显示回答预览
    preview_length = 300
    preview = full_response[:preview_length] + "..." if len(full_response) > preview_length else full_response
    print(f"\n💡 回答预览:\n{preview}")

    return {
        "id": question_id,
        "question": question,
        "mode": mode,
        "category": category,
        "first_response_time": first_response_time,
        "total_time": total_time,
        "total_chunks": total_chunks,
        "response_length": len(full_response),
        "tools_called": tools_called,
        "tools_count": len(tools_called),
        "sources_count": sources_count,
        "response_preview": preview,
        "success": True
    }


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🧪 规划咨询服务完整集成测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试问题数: {len(TEST_QUESTIONS)}")
    print("="*80)

    # 检查服务健康状态
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8003/health") as resp:
                if resp.status != 200:
                    print("❌ 服务不可用，请先启动规划服务")
                    return
                health = await resp.json()
                print(f"✅ 服务状态: {health['status']}")
                print(f"   服务名称: {health['service']}")
                print(f"   版本: {health['version']}")
                print(f"   知识库已加载: {health['knowledge_base_loaded']}")
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        return

    # 运行测试
    results = []
    async with aiohttp.ClientSession() as session:
        for i, question_data in enumerate(TEST_QUESTIONS, 1):
            print(f"\n\n进度: {i}/{len(TEST_QUESTIONS)}")

            result = await test_single_question(session, question_data)

            results.append(result)

            # 添加延迟，避免API限流
            if i < len(TEST_QUESTIONS):
                await asyncio.sleep(2)

    # 生成测试报告
    generate_report(results)


def generate_report(results: List[Dict[str, Any]], compare_with_baseline: bool = True):
    """
    生成测试报告

    Args:
        results: 测试结果列表
        compare_with_baseline: 是否与基线结果对比
    """
    print("\n\n" + "="*80)
    print("📊 测试报告")
    print("="*80)

    # 统计成功/失败
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]

    print(f"\n总测试数: {len(results)}")
    print(f"成功: {len(successful)}")
    print(f"失败: {len(failed)}")

    if failed:
        print(f"\n❌ 失败的问题:")
        for r in failed:
            print(f"  • {r['id']}: {r.get('error', '未知错误')}")

    # 性能统计
    if successful:
        first_response_times = [r["first_response_time"] for r in successful if r["first_response_time"]]
        total_times = [r["total_time"] for r in successful if r["total_time"]]
        total_chunks_list = [r["total_chunks"] for r in successful]
        response_lengths = [r["response_length"] for r in successful]
        sources_counts = [r["sources_count"] for r in successful]

        print(f"\n{'='*80}")
        print("性能统计")
        print(f"{'='*80}")

        print(f"\n首字响应时间:")
        if first_response_times:
            print(f"  • 平均: {sum(first_response_times)/len(first_response_times):.2f}s")
            print(f"  • 最快: {min(first_response_times):.2f}s")
            print(f"  • 最慢: {max(first_response_times):.2f}s")

        print(f"\n总响应时间:")
        if total_times:
            print(f"  • 平均: {sum(total_times)/len(total_times):.2f}s")
            print(f"  • 最快: {min(total_times):.2f}s")
            print(f"  • 最慢: {max(total_times):.2f}s")

        print(f"\n流式输出:")
        if total_chunks_list:
            print(f"  • 平均块数: {sum(total_chunks_list)//len(total_chunks_list)}")
            print(f"  • 最多块数: {max(total_chunks_list)}")

        print(f"\n回答长度:")
        if response_lengths:
            print(f"  • 平均长度: {sum(response_lengths)//len(response_lengths)} 字符")
            print(f"  • 最短: {min(response_lengths)} 字符")
            print(f"  • 最长: {max(response_lengths)} 字符")

        print(f"\n知识库引用:")
        print(f"  • 总引用数: {sum(sources_counts)}")
        print(f"  • 平均引用数: {sum(sources_counts)/len(sources_counts):.1f}")
        print(f"  • 引用成功率: {sum(1 for s in sources_counts if s > 0)/len(sources_counts)*100:.1f}%")

        # 详细结果表
        print(f"\n{'='*80}")
        print("详细结果")
        print(f"{'='*80}")
        print(f"\n{'ID':<5} {'首字响应':<10} {'总耗时':<10} {'块数':<8} {'长度':<8} {'引用':<6} {'工具':<20}")
        print("-" * 80)

        for r in successful:
            frt = f"{r['first_response_time']:.2f}s" if r['first_response_time'] else "N/A"
            tt = f"{r['total_time']:.2f}s" if r['total_time'] else "N/A"
            tools_str = ", ".join(r['tools_called'][:2]) + ("..." if len(r['tools_called']) > 2 else "")
            print(f"{r['id']:<5} {frt:<10} {tt:<10} {r['total_chunks']:<8} {r['response_length']:<8} {r['sources_count']:<6} {tools_str:<20}")

    # 对比分析
    print(f"\n{'='*80}")
    print("与之前测试报告的对比")
    print(f"{'='*80}")

    if successful and total_times:
        avg_time = sum(total_times) / len(total_times)
        print(f"\n平均总耗时: {avg_time:.2f}s (之前: 54.2s)")
        if avg_time < 54.2:
            print(f"  ✅ 改进: {54.2 - avg_time:.2f}s ({(54.2 - avg_time)/54.2*100:.1f}%)")
        else:
            print(f"  ⚠️  退化: {avg_time - 54.2:.2f}s ({(avg_time - 54.2)/54.2*100:.1f}%)")

        if first_response_times:
            avg_frt = sum(first_response_times) / len(first_response_times)
            print(f"\n平均首字响应: {avg_frt:.2f}s (之前: 0.28s)")
            if avg_frt < 0.28:
                print(f"  ✅ 改进: {0.28 - avg_frt:.2f}s")
            else:
                print(f"  ⚠️  退化: {avg_frt - 0.28:.2f}s")

        if sources_counts:
            source_success_rate = sum(1 for s in sources_counts if s > 0) / len(sources_counts) * 100
            print(f"\n知识库引用成功率: {source_success_rate:.1f}% (之前: 0%)")
            if source_success_rate > 0:
                print(f"  ✅ 改进: 引用功能已修复！")
            else:
                print(f"  ⚠️  引用功能仍有问题")

    print(f"\n{'='*80}")
    print("测试完成")
    print(f"{'='*80}\n")

    # ==================== 结果持久化 ====================
    print("\n" + "="*80)
    print("💾 保存测试结果")
    print("="*80)

    # 保存 JSON 结果
    json_path = save_results(results)

    # 生成 HTML 报告
    baseline_results = None
    if compare_with_baseline:
        # 尝试获取最新的历史结果作为基线
        latest = get_latest_results()
        if latest and "results" in latest:
            baseline_results = latest["results"]
            print(f"✅ 加载基线数据: {len(baseline_results)} 条历史记录")

    html_path = generate_html_report(results, baseline=baseline_results)

    print("\n" + "="*80)
    print("✅ 所有任务完成")
    print("="*80)
    print(f"📄 JSON 结果: {json_path}")
    print(f"📊 HTML 报告: {html_path}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())

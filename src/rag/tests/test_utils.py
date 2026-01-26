"""
测试工具模块
提供结果持久化、性能分析、报告生成等功能
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


# ==================== 结果持久化 ====================

def save_results(results: List[Dict[str, Any]], output_dir: Optional[Path] = None) -> Path:
    """
    保存测试结果到 JSON 文件

    Args:
        results: 测试结果列表
        output_dir: 输出目录（默认为 src/rag/tests/results/）

    Returns:
        保存的文件路径
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "results"

    # 确保目录存在
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"test_results_{timestamp}.json"

    # 添加元数据
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(results),
        "successful": len([r for r in results if r.get("success", False)]),
        "failed": len([r for r in results if not r.get("success", False)]),
        "results": results,
    }

    # 保存到文件
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 测试结果已保存: {filepath}")
    return filepath


def load_results(filepath: Path) -> Dict[str, Any]:
    """
    从 JSON 文件加载测试结果

    Args:
        filepath: JSON 文件路径

    Returns:
        包含测试结果和元数据的字典
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_latest_results(results_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    获取最新的测试结果文件

    Args:
        results_dir: 结果目录（默认为 src/rag/tests/results/）

    Returns:
        最新的测试结果，如果没有则返回 None
    """
    if results_dir is None:
        results_dir = Path(__file__).parent / "results"

    if not results_dir.exists():
        return None

    # 查找所有 test_results_*.json 文件
    files = sorted(results_dir.glob("test_results_*.json"), reverse=True)

    if not files:
        return None

    return load_results(files[0])


# ==================== 性能分析 ====================

def calculate_performance_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    计算性能统计指标

    Args:
        results: 测试结果列表

    Returns:
        性能统计字典
    """
    successful = [r for r in results if r.get("success", False)]

    if not successful:
        return {"error": "没有成功的测试结果"}

    # 提取各项指标
    first_response_times = [r["first_response_time"] for r in successful if r.get("first_response_time")]
    total_times = [r["total_time"] for r in successful if r.get("total_time")]
    total_chunks_list = [r["total_chunks"] for r in successful]
    response_lengths = [r["response_length"] for r in successful]
    sources_counts = [r["sources_count"] for r in successful]
    tools_counts = [r.get("tools_count", 0) for r in successful]

    stats = {
        "total_tests": len(results),
        "successful_tests": len(successful),
        "failed_tests": len(results) - len(successful),
        "success_rate": len(successful) / len(results) * 100 if results else 0,
    }

    # 首字响应时间统计
    if first_response_times:
        stats["first_response_time"] = {
            "avg": sum(first_response_times) / len(first_response_times),
            "min": min(first_response_times),
            "max": max(first_response_times),
            "count": len(first_response_times),
        }

    # 总响应时间统计
    if total_times:
        stats["total_time"] = {
            "avg": sum(total_times) / len(total_times),
            "min": min(total_times),
            "max": max(total_times),
            "count": len(total_times),
        }

    # 流式输出统计
    if total_chunks_list:
        stats["chunks"] = {
            "avg": sum(total_chunks_list) // len(total_chunks_list),
            "max": max(total_chunks_list),
        }

    # 回答长度统计
    if response_lengths:
        stats["response_length"] = {
            "avg": sum(response_lengths) // len(response_lengths),
            "min": min(response_lengths),
            "max": max(response_lengths),
        }

    # 知识库引用统计
    if sources_counts:
        stats["sources"] = {
            "total": sum(sources_counts),
            "avg": sum(sources_counts) / len(sources_counts),
            "success_rate": sum(1 for s in sources_counts if s > 0) / len(sources_counts) * 100,
        }

    # 工具调用统计
    if tools_counts:
        stats["tools"] = {
            "avg": sum(tools_counts) / len(tools_counts),
            "max": max(tools_counts),
        }

    return stats


def compare_with_baseline(
    current_results: List[Dict[str, Any]],
    baseline_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    将当前结果与基线结果进行对比

    Args:
        current_results: 当前测试结果
        baseline_results: 基线测试结果

    Returns:
        对比结果字典
    """
    current_stats = calculate_performance_stats(current_results)
    baseline_stats = calculate_performance_stats(baseline_results)

    comparison = {
        "timestamp": datetime.now().isoformat(),
        "current": current_stats,
        "baseline": baseline_stats,
        "changes": {},
    }

    # 对比关键指标
    key_metrics = ["first_response_time", "total_time", "sources", "tools"]

    for metric in key_metrics:
        if metric in current_stats and metric in baseline_stats:
            current_avg = current_stats[metric].get("avg", 0)
            baseline_avg = baseline_stats[metric].get("avg", 0)

            if baseline_avg > 0:
                change_percent = ((current_avg - baseline_avg) / baseline_avg) * 100
                comparison["changes"][metric] = {
                    "current": current_avg,
                    "baseline": baseline_avg,
                    "change_percent": change_percent,
                    "improved": change_percent < 0 if metric != "sources" else change_percent > 0,
                }

    return comparison


# ==================== HTML 报告生成 ====================

def generate_html_report(
    results: List[Dict[str, Any]],
    baseline: Optional[List[Dict[str, Any]]] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    生成 HTML 测试报告

    Args:
        results: 测试结果列表
        baseline: 基线结果（可选）
        output_dir: 输出目录（默认为 src/rag/tests/results/）

    Returns:
        生成的 HTML 文件路径
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "results"

    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"report_{timestamp}.html"

    # 计算统计数据
    stats = calculate_performance_stats(results)

    # 生成对比数据
    comparison = None
    if baseline:
        comparison = compare_with_baseline(results, baseline)

    # HTML 模板
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>规划咨询服务测试报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        .stat-card .label {{ color: #666; font-size: 14px; }}
        .section {{ padding: 30px; }}
        .section h2 {{
            font-size: 20px;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{ background: #f8f9fa; font-weight: 600; color: #333; }}
        tr:hover {{ background: #f8f9fa; }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .improvement {{ color: #28a745; font-weight: 600; }}
        .regression {{ color: #dc3545; font-weight: 600; }}
        .neutral {{ color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 规划咨询服务测试报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">总测试数</div>
                <div class="value">{stats.get('total_tests', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="label">成功率</div>
                <div class="value">{stats.get('success_rate', 0):.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="label">平均响应时间</div>
                <div class="value">{stats.get('total_time', {}).get('avg', 0):.1f}s</div>
            </div>
            <div class="stat-card">
                <div class="label">平均首字响应</div>
                <div class="value">{stats.get('first_response_time', {}).get('avg', 0):.2f}s</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 详细结果</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>问题</th>
                        <th>模式</th>
                        <th>首字响应</th>
                        <th>总耗时</th>
                        <th>状态</th>
                        <th>知识库引用</th>
                    </tr>
                </thead>
                <tbody>
"""

    # 添加测试结果行
    for r in results:
        question_preview = r.get("question", "")[:50] + "..." if len(r.get("question", "")) > 50 else r.get("question", "")
        status_badge = '<span class="badge badge-success">成功</span>' if r.get("success") else '<span class="badge badge-danger">失败</span>'

        html += f"""
                    <tr>
                        <td>{r.get('id', '')}</td>
                        <td title="{r.get('question', '')}">{question_preview}</td>
                        <td>{r.get('mode', '')}</td>
                        <td>{r.get('first_response_time', 0):.2f}s</td>
                        <td>{r.get('total_time', 0):.2f}s</td>
                        <td>{status_badge}</td>
                        <td>{r.get('sources_count', 0)} 条</td>
                    </tr>
"""

    # 添加基线对比（如果有）
    if comparison and "changes" in comparison:
        html += """
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>📈 与基线对比</h2>
            <table>
                <thead>
                    <tr>
                        <th>指标</th>
                        <th>当前值</th>
                        <th>基线值</th>
                        <th>变化</th>
                    </tr>
                </thead>
                <tbody>
"""

        for metric, data in comparison["changes"].items():
            metric_name = {
                "first_response_time": "首字响应时间",
                "total_time": "总响应时间",
                "sources": "知识库引用",
                "tools": "工具调用次数",
            }.get(metric, metric)

            change = data["change_percent"]
            if data.get("improved"):
                change_class = "improvement"
                change_symbol = "↓" if metric != "sources" else "↑"
                change_text = f"改进 {abs(change):.1f}%"
            else:
                change_class = "regression"
                change_symbol = "↑" if metric != "sources" else "↓"
                change_text = f"退化 {abs(change):.1f}%"

            html += f"""
                    <tr>
                        <td>{metric_name}</td>
                        <td>{data['current']:.2f}s</td>
                        <td>{data['baseline']:.2f}s</td>
                        <td class="{change_class}">{change_symbol} {change_text}</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

    # 保存 HTML 文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML 报告已生成: {filepath}")
    return filepath

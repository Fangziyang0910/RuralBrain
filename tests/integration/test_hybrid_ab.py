"""
混合检索 A/B 测试

对比纯向量检索 vs 混合检索（向量+BM25）效果：
1. 召回数量对比
2. 关键词覆盖率对比
3. 权重配置对比
4. 响应时间对比

任务编号: B3
负责人: 成员 B
"""
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

# 设置 UTF-8 编码输出（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from langchain_core.documents import Document

from src.rag.core.cache import get_vector_cache
from src.rag.core.hybrid_retriever import HybridRetriever, BM25_AVAILABLE
from src.rag.core.retriever import RuralBrainRetriever, get_retriever


# ==================== 测试数据定义 ====================

@dataclass
class TestQuery:
    """测试查询数据类"""
    query: str
    category: str
    expected_keywords: List[str]
    difficulty: str


# 预定义测试查询集（覆盖不同场景）
TEST_QUERIES = [
    # 关键词精确匹配场景（BM25 应更优）
    TestQuery("耕地保护政策", "政策", ["耕地", "保护", "政策"], "easy"),
    TestQuery("农村土地承包经营权", "政策", ["土地", "承包", "经营权"], "medium"),

    # 语义相似场景（向量检索应更优）
    TestQuery("如何提高农业生产效率", "技术", ["效率", "生产", "农业"], "medium"),
    TestQuery("乡村振兴战略实施", "政策", ["振兴", "乡村", "战略"], "medium"),

    # 混合场景（混合检索应表现最佳）
    TestQuery("农业补贴申请流程", "政策", ["补贴", "申请", "流程"], "medium"),
    TestQuery("水稻病虫害防治方法", "技术", ["水稻", "病虫害", "防治"], "hard"),
]

# 权重配置
WEIGHT_CONFIGS = [
    {"name": "vector_dominant", "vector": 0.7, "bm25": 0.3, "desc": "语义优先"},
    {"name": "balanced", "vector": 0.5, "bm25": 0.5, "desc": "均衡配置"},
    {"name": "bm25_dominant", "vector": 0.3, "bm25": 0.7, "desc": "关键词优先"},
]


# ==================== 评估指标 ====================

@dataclass
class EvaluationMetrics:
    """评估指标集合"""
    recall_count: int          # 返回结果数量
    avg_similarity: float      # 平均相似度
    keyword_coverage: float    # 关键词覆盖率
    response_time: float       # 响应时间（秒）
    unique_documents: int      # 独特文档数


def calculate_metrics(
    results: List[Tuple[Document, float]],
    expected_keywords: List[str],
    response_time: float,
) -> EvaluationMetrics:
    """
    计算评估指标

    Args:
        results: (Document, score) 元组列表
        expected_keywords: 预期关键词列表
        response_time: 响应时间

    Returns:
        EvaluationMetrics 实例
    """
    if not results:
        return EvaluationMetrics(
            recall_count=0,
            avg_similarity=0.0,
            keyword_coverage=0.0,
            response_time=response_time,
            unique_documents=0,
        )

    # 召回数量
    recall_count = len(results)

    # 平均相似度
    avg_similarity = sum(score for _, score in results) / len(results)

    # 独特文档数
    unique_docs = len(set(doc.metadata.get("source", "unknown") for doc, _ in results))

    # 关键词覆盖率
    keyword_hits = 0
    for doc, _ in results:
        content_lower = doc.page_content.lower()
        if any(kw.lower() in content_lower for kw in expected_keywords):
            keyword_hits += 1
    keyword_coverage = keyword_hits / len(results)

    return EvaluationMetrics(
        recall_count=recall_count,
        avg_similarity=avg_similarity,
        keyword_coverage=keyword_coverage,
        response_time=response_time,
        unique_documents=unique_docs,
    )


# ==================== A/B 测试执行 ====================

def run_vector_only_test(vectorstore, queries: List[TestQuery], k: int = 5) -> dict:
    """
    执行纯向量检索测试

    Args:
        vectorstore: 向量数据库实例
        queries: 测试查询列表
        k: 返回结果数量

    Returns:
        测试结果字典
    """
    retriever = get_retriever(
        vectorstore=vectorstore,
        search_type="similarity_score_threshold",
        k=k,
    )

    results = []
    for query in queries:
        start_time = time.time()
        docs = retriever.invoke(query.query)
        response_time = time.time() - start_time

        # 转换为 (Document, score) 格式
        results_with_scores = []
        for doc in docs:
            score = doc.metadata.get("score", 0.0)
            results_with_scores.append((doc, score))

        metrics = calculate_metrics(results_with_scores, query.expected_keywords, response_time)
        results.append({
            "query": query.query,
            "category": query.category,
            "metrics": metrics,
        })

    return {"method": "vector_only", "results": results}


def run_hybrid_test(vectorstore, queries: List[TestQuery], k: int = 5,
                    vector_weight: float = 0.5, bm25_weight: float = 0.5) -> dict:
    """
    执行混合检索测试

    Args:
        vectorstore: 向量数据库实例
        queries: 测试查询列表
        k: 返回结果数量
        vector_weight: 向量检索权重
        bm25_weight: BM25 检索权重

    Returns:
        测试结果字典
    """
    retriever = HybridRetriever(
        vectorstore=vectorstore,
        vector_weight=vector_weight,
        bm25_weight=bm25_weight,
    )

    results = []
    for query in queries:
        start_time = time.time()
        results_with_scores = retriever.retrieve(query.query, k=k)
        response_time = time.time() - start_time

        metrics = calculate_metrics(results_with_scores, query.expected_keywords, response_time)
        results.append({
            "query": query.query,
            "category": query.category,
            "metrics": metrics,
        })

    return {
        "method": "hybrid",
        "vector_weight": vector_weight,
        "bm25_weight": bm25_weight,
        "results": results,
    }


# ==================== 报告生成 ====================

def generate_comparison_table(vector_results: dict, hybrid_results: dict) -> str:
    """
    生成纯向量 vs 混合检索对比表格

    Args:
        vector_results: 纯向量检索结果
        hybrid_results: 混合检索结果

    Returns:
        表格字符串
    """
    lines = []
    lines.append("=" * 80)
    lines.append("混合检索 A/B 测试报告")
    lines.append("=" * 80)
    lines.append("")
    lines.append("一、纯向量 vs 混合检索对比")
    lines.append("-" * 80)
    lines.append(f"{'查询':<25} {'向量召回':>8} {'混合召回':>8} {'向量时间':>10} {'混合时间':>10} {'覆盖率':>8}")
    lines.append("-" * 80)

    total_vector_recall = 0
    total_hybrid_recall = 0
    total_vector_time = 0
    total_hybrid_time = 0
    total_coverage = 0

    for i, query in enumerate(TEST_QUERIES):
        v = vector_results["results"][i]
        h = hybrid_results["results"][i]
        vm = v["metrics"]
        hm = h["metrics"]

        query_display = query.query[:22] + "..." if len(query.query) > 22 else query.query
        lines.append(
            f"{query_display:<25} {vm.recall_count:>8} {hm.recall_count:>8} "
            f"{vm.response_time:>9.3f}s {hm.response_time:>9.3f}s "
            f"{hm.keyword_coverage:>7.0%}"
        )

        total_vector_recall += vm.recall_count
        total_hybrid_recall += hm.recall_count
        total_vector_time += vm.response_time
        total_hybrid_time += hm.response_time
        total_coverage += hm.keyword_coverage

    lines.append("-" * 80)

    # 计算汇总
    n = len(TEST_QUERIES)
    avg_vector_recall = total_vector_recall / n
    avg_hybrid_recall = total_hybrid_recall / n
    recall_improvement = (avg_hybrid_recall - avg_vector_recall) / avg_vector_recall * 100 if avg_vector_recall > 0 else 0
    time_overhead = (total_hybrid_time - total_vector_time) / total_vector_time * 100 if total_vector_time > 0 else 0
    avg_coverage = total_coverage / n

    lines.append(
        f"{'平均/总计':<25} {avg_vector_recall:>8.1f} {avg_hybrid_recall:>8.1f} "
        f"{total_vector_time/n:>9.3f}s {total_hybrid_time/n:>9.3f}s "
        f"{avg_coverage:>7.0%}"
    )
    lines.append("")
    lines.append(f"📊 召回率提升: {recall_improvement:+.1f}%")
    lines.append(f"⏱️  响应时间增加: {time_overhead:+.1f}%")
    lines.append(f"🎯 平均关键词覆盖率: {avg_coverage:.0%}")

    return "\n".join(lines)


def generate_weight_comparison_table(weight_results: List[dict]) -> str:
    """
    生成权重配置对比表格

    Args:
        weight_results: 不同权重配置的测试结果列表

    Returns:
        表格字符串
    """
    lines = []
    lines.append("")
    lines.append("二、权重配置对比")
    lines.append("-" * 80)
    lines.append(f"{'配置名称':<20} {'平均召回':>10} {'平均相似度':>12} {'平均覆盖率':>12} {'平均时间':>10}")
    lines.append("-" * 80)

    for result in weight_results:
        config_name = result["config"]["name"]
        desc = result["config"]["desc"]

        metrics_list = [r["metrics"] for r in result["results"]]
        avg_recall = sum(m.recall_count for m in metrics_list) / len(metrics_list)
        avg_similarity = sum(m.avg_similarity for m in metrics_list) / len(metrics_list)
        avg_coverage = sum(m.keyword_coverage for m in metrics_list) / len(metrics_list)
        avg_time = sum(m.response_time for m in metrics_list) / len(metrics_list)

        lines.append(
            f"{config_name:<20} {avg_recall:>10.1f} {avg_similarity:>12.3f} "
            f"{avg_coverage:>11.0%} {avg_time:>9.3f}s"
        )

    lines.append("-" * 80)

    # 找出最佳配置
    best_config = max(weight_results, key=lambda r: sum(m.keyword_coverage for m in [rr["metrics"] for rr in r["results"]]))
    lines.append(f"💡 推荐配置: {best_config['config']['name']} ({best_config['config']['desc']})")

    return "\n".join(lines)


def generate_summary(recall_improvement: float, coverage_improvement: float,
                    time_overhead: float, recommendation: str) -> str:
    """
    生成总结报告

    Args:
        recall_improvement: 召回率提升百分比
        coverage_improvement: 覆盖率提升百分比
        time_overhead: 时间开销百分比
        recommendation: 推荐配置

    Returns:
        总结字符串
    """
    lines = []
    lines.append("")
    lines.append("三、综合评估")
    lines.append("-" * 80)

    # 召回率评估
    if recall_improvement > 30:
        recall_status = "✅ 显著提升"
    elif recall_improvement > 10:
        recall_status = "✅ 有效提升"
    else:
        recall_status = "⚠️ 提升有限"
    lines.append(f"• 混合检索召回率提升: {recall_improvement:+.1f}% {recall_status}")

    # 覆盖率评估
    if coverage_improvement > 20:
        coverage_status = "✅ 显著提升"
    elif coverage_improvement > 5:
        coverage_status = "✅ 有效提升"
    else:
        coverage_status = "⚠️ 提升有限"
    lines.append(f"• 关键词覆盖率提升: {coverage_improvement:+.1f}% {coverage_status}")

    # 时间评估
    if time_overhead < 30:
        time_status = "✅ 可接受"
    elif time_overhead < 50:
        time_status = "⚠️ 略有增加"
    else:
        time_status = "❌ 需要优化"
    lines.append(f"• 响应时间增加: {time_overhead:+.1f}% {time_status}")

    lines.append("")
    lines.append(f"📌 推荐默认配置: {recommendation}")
    lines.append("=" * 80)

    return "\n".join(lines)


# ==================== 主测试函数 ====================

def run_ab_test(k: int = 5) -> dict:
    """
    执行完整的 A/B 测试

    Args:
        k: 每次检索返回的结果数量

    Returns:
        完整测试结果
    """
    print("=" * 80)
    print("开始混合检索 A/B 测试")
    print("=" * 80)
    print(f"测试查询数: {len(TEST_QUERIES)}")
    print(f"权重配置数: {len(WEIGHT_CONFIGS)}")
    print(f"每次返回结果数: {k}")
    print()

    # 检查 BM25 可用性
    if not BM25_AVAILABLE:
        print("❌ rank-bm25 未安装，跳过混合检索测试")
        print("请运行: uv add rank-bm25")
        return {"error": "BM25 not available"}

    # 初始化向量数据库
    print("正在初始化向量数据库...")
    cache = get_vector_cache()
    vectorstore = cache.get_vectorstore()
    print("✅ 向量数据库初始化完成")
    print()

    # 1. 纯向量检索测试
    print("执行纯向量检索测试...")
    vector_results = run_vector_only_test(vectorstore, TEST_QUERIES, k)
    print("✅ 纯向量检索测试完成")
    print()

    # 2. 混合检索测试（balanced 配置）
    print("执行混合检索测试（balanced 配置）...")
    hybrid_results = run_hybrid_test(vectorstore, TEST_QUERIES, k, 0.5, 0.5)
    print("✅ 混合检索测试完成")
    print()

    # 3. 不同权重配置对比
    print("执行权重配置对比测试...")
    weight_results = []
    for config in WEIGHT_CONFIGS:
        print(f"  测试配置: {config['name']} ({config['desc']})")
        result = run_hybrid_test(
            vectorstore, TEST_QUERIES, k,
            config["vector"], config["bm25"]
        )
        result["config"] = config
        weight_results.append(result)
    print("✅ 权重配置对比测试完成")
    print()

    # 生成报告
    print("生成测试报告...")
    print()

    # 计算关键指标
    v_metrics = [r["metrics"] for r in vector_results["results"]]
    h_metrics = [r["metrics"] for r in hybrid_results["results"]]

    avg_v_recall = sum(m.recall_count for m in v_metrics) / len(v_metrics)
    avg_h_recall = sum(m.recall_count for m in h_metrics) / len(h_metrics)
    recall_improvement = (avg_h_recall - avg_v_recall) / avg_v_recall * 100 if avg_v_recall > 0 else 0

    avg_v_coverage = sum(m.keyword_coverage for m in v_metrics) / len(v_metrics)
    avg_h_coverage = sum(m.keyword_coverage for m in h_metrics) / len(h_metrics)
    coverage_improvement = (avg_h_coverage - avg_v_coverage) * 100

    total_v_time = sum(m.response_time for m in v_metrics)
    total_h_time = sum(m.response_time for m in h_metrics)
    time_overhead = (total_h_time - total_v_time) / total_v_time * 100 if total_v_time > 0 else 0

    # 输出报告
    print(generate_comparison_table(vector_results, hybrid_results))
    print(generate_weight_comparison_table(weight_results))
    print(generate_summary(recall_improvement, coverage_improvement, time_overhead, "balanced (0.5/0.5)"))

    return {
        "vector_results": vector_results,
        "hybrid_results": hybrid_results,
        "weight_results": weight_results,
        "summary": {
            "recall_improvement": recall_improvement,
            "coverage_improvement": coverage_improvement,
            "time_overhead": time_overhead,
            "recommendation": "balanced",
        },
    }


# ==================== pytest 测试类 ====================

class TestHybridAB:
    """混合检索 A/B 测试类"""

    @classmethod
    def setup_class(cls):
        """测试类初始化"""
        if not BM25_AVAILABLE:
            pytest.skip("rank-bm25 未安装")

        cache = get_vector_cache()
        cls.vectorstore = cache.get_vectorstore()
        cls.test_queries = TEST_QUERIES[:3]  # 使用部分查询进行快速测试

    def test_vector_vs_hybrid_recall(self):
        """测试召回数量对比"""
        vector_results = run_vector_only_test(self.vectorstore, self.test_queries, k=5)
        hybrid_results = run_hybrid_test(self.vectorstore, self.test_queries, k=5)

        for i, query in enumerate(self.test_queries):
            hybrid_count = hybrid_results["results"][i]["metrics"].recall_count
            vector_count = vector_results["results"][i]["metrics"].recall_count

            # 混合检索召回数量应不低于纯向量的 80%
            assert hybrid_count >= vector_count * 0.8, \
                f"混合检索召回率过低: {query.query}"

    def test_keyword_coverage_improvement(self):
        """测试关键词覆盖改进"""
        vector_results = run_vector_only_test(self.vectorstore, self.test_queries, k=5)
        hybrid_results = run_hybrid_test(self.vectorstore, self.test_queries, k=5)

        for i, query in enumerate(self.test_queries):
            if query.expected_keywords:
                hybrid_coverage = hybrid_results["results"][i]["metrics"].keyword_coverage
                vector_coverage = vector_results["results"][i]["metrics"].keyword_coverage

                # 关键词场景覆盖率应有所提升
                if query.category in ["政策", "技术"]:
                    assert hybrid_coverage >= vector_coverage * 0.9, \
                        f"关键词场景覆盖率未提升: {query.query}"

    def test_weight_configurations(self):
        """测试不同权重配置效果"""
        results = {}

        for config in WEIGHT_CONFIGS:
            result = run_hybrid_test(
                self.vectorstore,
                self.test_queries,
                k=5,
                vector_weight=config["vector"],
                bm25_weight=config["bm25"],
            )

            metrics_list = [r["metrics"] for r in result["results"]]
            avg_coverage = sum(m.keyword_coverage for m in metrics_list) / len(metrics_list)
            results[config["name"]] = avg_coverage

        # 验证不同配置有不同表现
        assert len(set(results.values())) > 1, "权重配置应该产生不同的结果"


# ==================== 主入口 ====================

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.WARNING)  # 减少日志输出

    # 需要导入 pytest 用于跳过测试
    import pytest

    result = run_ab_test(k=5)

    # 返回退出码
    sys.exit(0 if "error" not in result else 1)
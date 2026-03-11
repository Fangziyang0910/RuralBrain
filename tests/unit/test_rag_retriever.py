"""
测试 RuralBrainRetriever 标准检索器

验证符合 LangChain 标准的检索器功能：
1. 标准检索器接口实现
2. 评分过滤功能
3. 多种检索策略（similarity、mmr、similarity_score_threshold）
4. 上下文扩展功能
5. 与现有工具的兼容性
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

# 加载环境变量（必须在导入 src.rag.config 之前）
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from src.rag.core.retriever import (
    RuralBrainRetriever,
    get_retriever,
    SearchType,
)
from src.rag.core.cache import get_vector_cache
from src.rag.config import (
    RETRIEVE_SCORE_THRESHOLD,
    MMR_LAMBDA_MULT,
)


def test_retriever_creation():
    """测试 1: 检索器创建"""
    print("=" * 60)
    print("测试 1: 检索器创建")
    print("=" * 60)

    # 获取向量数据库
    cache = get_vector_cache()
    vectorstore = cache.get_vectorstore()

    # 创建检索器（使用默认配置）
    retriever = RuralBrainRetriever(
        vectorstore=vectorstore,
    )

    assert retriever.vectorstore is vectorstore, "向量数据库应正确设置"
    print(f"  ✓ 向量数据库已设置")

    assert retriever.search_type == "similarity_score_threshold", "默认检索策略应为 similarity_score_threshold"
    print(f"  ✓ 默认检索策略: {retriever.search_type}")

    assert retriever.k == 5, "默认 k 应为 5"
    print(f"  ✓ 默认 k = 5")

    assert retriever.score_threshold == RETRIEVE_SCORE_THRESHOLD, f"默认阈值应为 {RETRIEVE_SCORE_THRESHOLD}"
    print(f"  ✓ 默认评分阈值: {retriever.score_threshold}")

    return True


def test_retriever_custom_config():
    """测试 2: 自定义配置"""
    print("\n" + "=" * 60)
    print("测试 2: 自定义配置")
    print("=" * 60)

    cache = get_vector_cache()
    vectorstore = cache.get_vectorstore()

    # 创建自定义配置的检索器
    retriever = RuralBrainRetriever(
        vectorstore=vectorstore,
        search_type="mmr",
        k=3,
        score_threshold=0.5,
        lambda_mult=0.8,
    )

    assert retriever.search_type == "mmr", "检索策略应为 mmr"
    print(f"  ✓ 检索策略: {retriever.search_type}")

    assert retriever.k == 3, "k 应为 3"
    print(f"  ✓ k = 3")

    assert retriever.score_threshold == 0.5, "评分阈值应为 0.5"
    print(f"  ✓ 评分阈值: {retriever.score_threshold}")

    assert retriever.lambda_mult == 0.8, "lambda_mult 应为 0.8"
    print(f"  ✓ lambda_mult = {retriever.lambda_mult}")

    return True


def test_convenience_function():
    """测试 3: 便捷函数 get_retriever"""
    print("\n" + "=" * 60)
    print("测试 3: 便捷函数 get_retriever")
    print("=" * 60)

    cache = get_vector_cache()
    vectorstore = cache.get_vectorstore()

    # 使用便捷函数创建检索器
    retriever = get_retriever(
        vectorstore=vectorstore,
        search_type="similarity",
        k=5,
    )

    assert isinstance(retriever, RuralBrainRetriever), "应返回 RuralBrainRetriever 实例"
    print(f"  ✓ 返回 RuralBrainRetriever 实例")

    assert retriever.search_type == "similarity", "检索策略应为 similarity"
    print(f"  ✓ 检索策略: {retriever.search_type}")

    return True


def test_basic_retrieval():
    """测试 4: 基础检索功能"""
    print("\n" + "=" * 60)
    print("测试 4: 基础检索功能")
    print("=" * 60)

    cache = get_vector_cache()
    vectorstore = cache.get_vectorstore()

    retriever = get_retriever(
        vectorstore=vectorstore,
        search_type="similarity",
        k=3,
    )

    # 执行检索
    query = "乡村规划"
    results = retriever.invoke(query)

    assert isinstance(results, list), "结果应为列表"
    print(f"  ✓ 返回结果类型: list")

    assert len(results) <= 3, f"结果数量不应超过 k=3，实际: {len(results)}"
    print(f"  ✓ 结果数量: {len(results)}")

    if results:
        from langchain_core.documents import Document
        assert all(isinstance(doc, Document) for doc in results), "所有结果应为 Document 对象"
        print(f"  ✓ 所有结果为 Document 对象")

        # 检查第一个结果
        first_doc = results[0]
        assert hasattr(first_doc, 'page_content'), "Document 应有 page_content 属性"
        assert hasattr(first_doc, 'metadata'), "Document 应有 metadata 属性"
        print(f"  ✓ Document 结构正确")
        print(f"  ✓ 第一个结果预览: {first_doc.page_content[:50]}...")

    return True


def test_score_threshold_filtering():
    """测试 5: 评分过滤功能"""
    print("\n" + "=" * 60)
    print("测试 5: 评分过滤功能")
    print("=" * 60)

    cache = get_vector_cache()
    vectorstore = cache.get_vectorstore()

    # 创建带评分过滤的检索器
    retriever = get_retriever(
        vectorstore=vectorstore,
        search_type="similarity_score_threshold",
        k=5,
        score_threshold=0.3,  # 使用较低阈值以获得更多结果
    )

    query = "乡村发展"
    results = retriever.invoke(query)

    print(f"  ✓ 检索完成，返回 {len(results)} 个结果")

    if results:
        # 检查是否所有结果都有评分
        scores = []
        for doc in results:
            score = doc.metadata.get("score")
            if score is not None:
                scores.append(score)
                assert score >= 0.3, f"评分 {score} 应 >= 阈值 0.3"

        if scores:
            print(f"  ✓ 所有通过过滤的结果评分 >= 0.3")
            print(f"  ✓ 评分范围: {min(scores):.3f} - {max(scores):.3f}")
        else:
            print(f"  ⚠️  未找到带评分的结果（可能使用了不同检索策略）")

    return True


def test_mmr_retrieval():
    """测试 6: MMR 检索"""
    print("\n" + "=" * 60)
    print("测试 6: MMR 检索")
    print("=" * 60)

    cache = get_vector_cache()
    vectorstore = cache.get_vectorstore()

    # 创建 MMR 检索器
    retriever = get_retriever(
        vectorstore=vectorstore,
        search_type="mmr",
        k=3,
    )

    query = "农业现代化"
    results = retriever.invoke(query)

    assert isinstance(results, list), "结果应为列表"
    print(f"  ✓ MMR 检索完成，返回 {len(results)} 个结果")

    if results:
        from langchain_core.documents import Document
        assert all(isinstance(doc, Document) for doc in results), "所有结果应为 Document 对象"
        print(f"  ✓ 所有结果为 Document 对象")

    return True


def test_cache_integration():
    """测试 7: 缓存集成模块"""
    print("\n" + "=" * 60)
    print("测试 7: 缓存集成模块")
    print("=" * 60)

    cache = get_vector_cache()

    # 测试通过缓存获取检索器
    retriever = cache.get_retriever(
        search_type="similarity",
        k=3,
    )

    assert isinstance(retriever, RuralBrainRetriever), "应返回 RuralBrainRetriever 实例"
    print(f"  ✓ 通过缓存获取检索器成功")

    # 检查配置是否正确传递
    assert retriever.k == 3, "k 应为 3"
    print(f"  ✓ 配置正确传递 (k=3)")

    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始测试 RuralBrainRetriever")
    print("=" * 60)

    tests = [
        test_retriever_creation,
        test_retriever_custom_config,
        test_convenience_function,
        test_basic_retrieval,
        test_score_threshold_filtering,
        test_mmr_retrieval,
        test_cache_integration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"\n  ✗ 测试失败: {test.__name__}")
            print(f"    错误: {e}")
        except Exception as e:
            failed += 1
            print(f"\n  ✗ 测试异常: {test.__name__}")
            print(f"    错误: {e}")

    print("\n" + "=" * 60)
    print(f"测试完成: 通过 {passed}/{len(tests)}，失败 {failed}/{len(tests)}")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    success = run_all_tests()
    sys.exit(0 if success else 1)

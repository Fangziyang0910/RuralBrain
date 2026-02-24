"""
RAG 知识库模块功能测试
测试所有核心功能是否正常工作
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.core.context_manager import get_context_manager
from src.rag.core.cache import get_vector_cache
from src.rag.core.tools import (
    list_available_documents,
    get_document_overview,
    search_key_points,
    search_knowledge,
)
from src.rag.config import (
    CHROMA_PERSIST_DIR,
    DATA_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)


def test_singleton_pattern():
    """测试单例模式"""
    print("=" * 60)
    print("测试 1: 单例模式")
    print("=" * 60)

    # 测试 VectorStoreCache 单例
    cache1 = get_vector_cache()
    cache2 = get_vector_cache()
    print(f"\nVectorStoreCache 单例: {cache1 is cache2}")

    # 测试 DocumentContextManager 单例
    cm1 = get_context_manager()
    cm2 = get_context_manager()
    print(f"DocumentContextManager 单例: {cm1 is cm2}")

    # 测试缓存统计
    stats = cache1.get_cache_stats()
    print(f"\n缓存统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    return True


def test_knowledge_base_loaded():
    """测试知识库是否已加载"""
    print("\n" + "=" * 60)
    print("测试 2: 知识库加载状态")
    print("=" * 60)

    try:
        cm = get_context_manager()
        cm._ensure_loaded()

        print(f"\n✅ 知识库已加载")
        print(f"文档数量: {len(cm.doc_index)}")

        if cm.doc_index:
            print(f"\n可用文档:")
            for source in list(cm.doc_index.keys())[:5]:
                print(f"  - {source}")

        return len(cm.doc_index) > 0

    except Exception as e:
        print(f"\n❌ 知识库未加载: {e}")
        print(f"  提示: 请先构建知识库")
        return False


def test_document_list():
    """测试文档列表工具"""
    print("\n" + "=" * 60)
    print("测试 3: 文档列表工具")
    print("=" * 60)

    try:
        result = list_available_documents()
        print(f"\n结果类型: {type(result)}")

        if isinstance(result, str):
            print(f"\n{result}")
            return "未找到文档" not in result
        elif isinstance(result, list):
            print(f"\n文档列表:")
            for item in result[:5]:
                print(f"  - {item}")
            return len(result) > 0
        else:
            print(f"\n未知格式: {result}")
            return False

    except Exception as e:
        print(f"\n❌ 工具调用失败: {e}")
        return False


def test_document_overview():
    """测试文档概览工具"""
    print("\n" + "=" * 60)
    print("测试 4: 文档概览工具")
    print("=" * 60)

    try:
        cm = get_context_manager()
        cm._ensure_loaded()

        if not cm.doc_index:
            print("\n⚠️  知识库为空，跳过此测试")
            return True

        # 获取第一个文档
        first_doc = list(cm.doc_index.keys())[0]
        print(f"\n测试文档: {first_doc}")

        result = get_document_overview(first_doc)
        print(f"\n结果类型: {type(result)}")

        if isinstance(result, dict):
            print(f"\n文档概览:")
            for key, value in result.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {key}: {value[:100]}...")
                else:
                    print(f"  {key}: {value}")
            return True
        elif isinstance(result, str):
            print(f"\n{result}")
            return "未找到" not in result
        else:
            print(f"\n未知格式: {result}")
            return False

    except Exception as e:
        print(f"\n❌ 工具调用失败: {e}")
        return False


def test_knowledge_search():
    """测试知识库搜索工具"""
    print("\n" + "=" * 60)
    print("测试 5: 知识库搜索工具")
    print("=" * 60)

    try:
        test_query = "罗浮山的发展定位"
        print(f"\n测试查询: {test_query}")

        result = search_knowledge(
            query=test_query,
            top_k=3,
            context_mode="minimal"
        )

        print(f"\n结果类型: {type(result)}")

        if isinstance(result, str):
            print(f"\n{result}")
            # 检查是否真的返回了内容
            return len(result) > 50
        elif isinstance(result, dict):
            print(f"\n结果: {result}")
            return True
        else:
            print(f"\n未知格式: {result}")
            return False

    except Exception as e:
        print(f"\n❌ 工具调用失败: {e}")
        return False


def test_key_points_search():
    """测试关键点搜索工具"""
    print("\n" + "=" * 60)
    print("测试 6: 关键点搜索工具")
    print("=" * 60)

    try:
        test_query = "发展"
        print(f"\n测试查询: {test_query}")

        result = search_key_points(test_query)
        print(f"\n结果类型: {type(result)}")

        if isinstance(result, dict):
            print(f"\n关键点数量: {result.get('total_matches', 0)}")
            print(f"\n匹配的关键点:")
            matches = result.get('matches', [])
            for match in matches[:5]:
                print(f"  - {match.get('point', match)[:100]}...")
            return len(matches) > 0
        elif isinstance(result, str):
            print(f"\n{result}")
            return "未找到" not in result
        else:
            print(f"\n未知格式: {result}")
            return False

    except Exception as e:
        print(f"\n❌ 工具调用失败: {e}")
        return False


def test_config():
    """测试配置加载"""
    print("\n" + "=" * 60)
    print("测试 7: 配置加载")
    print("=" * 60)

    print(f"\nCHROMA_PERSIST_DIR: {CHROMA_PERSIST_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"CHUNK_SIZE: {CHUNK_SIZE}")
    print(f"CHUNK_OVERLAP: {CHUNK_OVERLAP}")

    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🚀 RAG 知识库模块功能测试")
    print("=" * 60)

    results = {
        "单例模式": False,
        "知识库加载状态": False,
        "文档列表工具": False,
        "文档概览工具": False,
        "知识库搜索工具": False,
        "关键点搜索工具": False,
        "配置加载": False,
    }

    # 1. 测试单例模式
    results["单例模式"] = test_singleton_pattern()

    # 2. 测试配置加载
    results["配置加载"] = test_config()

    # 3. 测试知识库加载状态
    kb_loaded = test_knowledge_base_loaded()

    # 如果知识库已加载，继续测试其他功能
    if kb_loaded:
        results["知识库加载状态"] = True
        results["文档列表工具"] = test_document_list()
        results["文档概览工具"] = test_document_overview()
        results["知识库搜索工具"] = test_knowledge_search()
        results["关键点搜索工具"] = test_key_points_search()
    else:
        print("\n⚠️  知识库未加载，跳过部分测试")

    # 输出测试结果汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "⚠️ 跳过/失败"
        print(f"{test_name}: {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())

    print(f"\n总计: {passed_tests}/{total_tests} 个测试通过")

    if passed_tests == total_tests:
        print("\n🎉 所有功能测试通过！")
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试未通过")


if __name__ == "__main__":
    main()

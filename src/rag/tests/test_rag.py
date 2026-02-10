"""
RAG 知识库模块功能测试
测试所有核心功能是否正常工作
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.utils import load_documents_from_directory, PPTXLoader, TextFileLoader
from src.rag.config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from langchain_text_splitters import RecursiveCharacterTextSplitter


def test_document_loading():
    """测试文档加载功能"""
    print("="*60)
    print("测试 1: 文档加载功能")
    print("="*60)

    try:
        # 测试从目录批量加载
        documents = load_documents_from_directory(
            DATA_DIR,
            file_extensions=[".txt"]
        )

        print(f"\n✅ 成功加载 {len(documents)} 个文档片段")

        # 显示前几个文档
        for i, doc in enumerate(documents[:3]):
            print(f"\n--- 文档 {i+1} ---")
            print(f"来源: {doc.metadata.get('source')}")
            print(f"位置: {doc.metadata.get('paragraph', doc.metadata.get('page', '未知'))}")
            print(f"内容长度: {len(doc.page_content)} 字符")
            print(f"内容预览: {doc.page_content[:100]}...")

        return documents

    except Exception as e:
        print(f"\n❌ 文档加载失败: {e}")
        return None


def test_text_splitting(documents):
    """测试文档切分功能"""
    print("\n" + "="*60)
    print("测试 2: 文档切分功能")
    print("="*60)

    try:
        print(f"\n配置: chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            add_start_index=True,
        )

        splits = text_splitter.split_documents(documents)
        print(f"\n✅ 成功切分为 {len(splits)} 个切片")

        # 显示前几个切片
        for i, split in enumerate(splits[:3]):
            print(f"\n--- 切片 {i+1} ---")
            print(f"来源: {split.metadata.get('source')}")
            print(f"内容长度: {len(split.page_content)} 字符")
            print(f"内容预览: {split.page_content[:150]}...")

        return splits

    except Exception as e:
        print(f"\n❌ 文档切分失败: {e}")
        return None


def test_slice_inspector(splits):
    """测试切片可视化工具"""
    print("\n" + "="*60)
    print("测试 3: 切片可视化工具")
    print("="*60)

    try:
        from src.rag.visualize import SliceInspector

        inspector = SliceInspector(splits)

        print("\n📊 切片统计:")
        inspector.print_summary()

        print("\n🔍 查看前 2 个切片的详情:")
        inspector.print_slice_details(start_idx=0, end_idx=2, show_content=False)

        print("\n⚠️  潜在问题检测:")
        inspector.print_issues(max_issues=5)

        # 导出 JSON
        json_path = DATA_DIR / "test_slices_analysis.json"
        inspector.export_to_json(json_path)
        print(f"\n✅ 切片分析已导出到: {json_path}")

        return True

    except Exception as e:
        print(f"\n❌ 切片可视化失败: {e}")
        return False


def test_vector_store_build(splits):
    """测试向量库构建"""
    print("\n" + "="*60)
    print("测试 4: 向量库构建")
    print("="*60)

    try:
        from src.rag.build import build_vector_store

        vectorstore = build_vector_store(splits)
        print("\n✅ 向量库构建成功")

        return vectorstore

    except Exception as e:
        print(f"\n❌ 向量库构建失败: {e}")
        return None


def test_basic_retrieval():
    """测试基础检索功能"""
    print("\n" + "="*60)
    print("测试 5: 基础检索功能")
    print("="*60)

    try:
        from src.rag.core.tools import retrieve_planning_knowledge

        # 测试查询
        test_queries = [
            "罗浮山的发展定位是什么？",
            "博罗县的现代农业有什么特点？",
            "如何保护罗浮山的生态环境？"
        ]

        for query in test_queries:
            print(f"\n🔍 查询: {query}")
            result = retrieve_planning_knowledge(query, top_k=2)
            print(f"\n📝 结果预览 (前 500 字符):")
            print(result[:500] + "..." if len(result) > 500 else result)
            print("-" * 60)

        print("\n✅ 基础检索功能正常")

        return True

    except Exception as e:
        print(f"\n❌ 基础检索失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata_filter_retrieval():
    """测试元数据过滤检索"""
    print("\n" + "="*60)
    print("测试 6: 元数据过滤检索")
    print("="*60)

    try:
        from src.rag.core.tools import retrieve_with_metadata

        # 测试元数据过滤
        query = "发展规划"
        source = "test_planning.txt"

        print(f"\n🔍 查询: {query}")
        print(f"🎯 过滤条件: source={source}")

        results = retrieve_with_metadata(query, top_k=3, source_filter=source)

        print(f"\n✅ 检索到 {len(results)} 个结果")

        for i, doc in enumerate(results[:2]):
            print(f"\n--- 结果 {i+1} ---")
            print(f"来源: {doc.metadata.get('source')}")
            print(f"位置: {doc.metadata.get('paragraph', doc.metadata.get('page'))}")
            print(f"内容: {doc.page_content[:200]}...")

        return True

    except Exception as e:
        print(f"\n❌ 元数据过滤检索失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_langchain_tool():
    """测试 LangChain Tool 集成"""
    print("\n" + "="*60)
    print("测试 7: LangChain Tool 集成")
    print("="*60)

    try:
        from src.rag.core.tools import planning_knowledge_tool

        print(f"\n🔧 Tool 名称: {planning_knowledge_tool.name}")
        print(f"📝 Tool 描述: {planning_knowledge_tool.description[:200]}...")

        # 测试工具调用
        query = "罗浮山的旅游产业有什么特色？"
        print(f"\n🔍 调用 Tool: {query}")

        result = planning_knowledge_tool.run(query)
        print(f"\n📝 结果预览 (前 500 字符):")
        print(result[:500] + "..." if len(result) > 500 else result)

        print("\n✅ LangChain Tool 集成正常")

        return True

    except Exception as e:
        print(f"\n❌ LangChain Tool 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🚀 RAG 知识库模块功能测试")
    print("="*60)

    results = {
        "文档加载": False,
        "文档切分": False,
        "切片可视化": False,
        "向量库构建": False,
        "基础检索": False,
        "元数据过滤": False,
        "LangChain Tool": False,
    }

    # 1. 测试文档加载
    documents = test_document_loading()
    if documents:
        results["文档加载"] = True

        # 2. 测试文档切分
        splits = test_text_splitting(documents)
        if splits:
            results["文档切分"] = True

            # 3. 测试切片可视化
            if test_slice_inspector(splits):
                results["切片可视化"] = True

            # 4. 测试向量库构建
            vectorstore = test_vector_store_build(splits)
            if vectorstore:
                results["向量库构建"] = True

                # 5-7. 测试检索功能
                results["基础检索"] = test_basic_retrieval()
                results["元数据过滤"] = test_metadata_filter_retrieval()
                results["LangChain Tool"] = test_langchain_tool()

    # 输出测试结果汇总
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())

    print(f"\n总计: {passed_tests}/{total_tests} 个测试通过")

    if passed_tests == total_tests:
        print("\n🎉 所有功能测试通过！")
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试失败，请检查")


if __name__ == "__main__":
    main()

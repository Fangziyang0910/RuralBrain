"""
测试阶段1新功能：全文上下文查询
验证文档上下文管理器和新增的 Agent 工具
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.core.context_manager import DocumentContextManager, get_context_manager
from src.rag.core.tools import (
    get_full_document,
    get_chapter_by_header,
    list_available_documents,
    retrieve_planning_knowledge,
)


def test_context_manager():
    """测试文档上下文管理器"""
    print("="*60)
    print("测试 1: DocumentContextManager")
    print("="*60)

    try:
        cm = get_context_manager()

        # 测试列出文档
        print("\n📋 测试列出所有文档...")
        result = list_available_documents()
        print(result)

        if not cm.doc_index:
            print("\n⚠️  没有找到文档索引，请先运行 build.py 构建知识库")
            return False

        # 获取第一个文档进行测试
        first_source = list(cm.doc_index.keys())[0]
        print(f"\n📄 测试获取完整文档: {first_source}")

        result = get_full_document(first_source)
        print(f"✅ 成功获取文档，内容长度: {len(result)} 字符")
        print(f"预览前500字符:\n{result[:500]}...")

        # 测试章节查询（如果有标题结构）
        print(f"\n📖 测试章节查询...")
        result = cm.get_chapter_by_header(first_source, "第一章")
        if "error" not in result:
            print(f"✅ 找到章节: {result['chapter_title']}")
            print(f"内容长度: {len(result['content'])} 字符")
        else:
            print(f"ℹ️  未找到标题（可能是按段落切分的文档）")

        return True

    except FileNotFoundError as e:
        print(f"❌ 索引文件不存在: {e}")
        print(f"请先运行: python src/rag/build.py")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retrieval_with_context():
    """测试带上下文的检索"""
    print("\n" + "="*60)
    print("测试 2: 带上下文的检索")
    print("="*60)

    try:
        # 测试查询
        query = "罗浮山的发展定位"
        print(f"\n🔍 测试查询: {query}")

        # 不带上下文的检索
        print("\n--- 不带上下文 ---")
        result_no_ctx = retrieve_planning_knowledge(query, with_context=False)
        print(result_no_ctx[:500] + "...")

        # 带上下文的检索
        print("\n--- 带上下文 ---")
        result_with_ctx = retrieve_planning_knowledge(query, with_context=True, context_chars=200)
        print(result_with_ctx[:800] + "...")

        # 比较结果长度
        print(f"\n📊 对比:")
        print(f"   不带上下文: {len(result_no_ctx)} 字符")
        print(f"   带上下文: {len(result_with_ctx)} 字符")
        print(f"   上下文增益: +{len(result_with_ctx) - len(result_no_ctx)} 字符")

        return True

    except Exception as e:
        print(f"❌ 检索测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chapter_query():
    """测试章节查询工具"""
    print("\n" + "="*60)
    print("测试 3: 章节查询工具")
    print("="*60)

    try:
        cm = get_context_manager()

        if not cm.doc_index:
            print("⚠️  没有可用文档")
            return False

        # 获取第一个文档
        first_source = list(cm.doc_index.keys())[0]

        # 测试不同的查询模式
        patterns = ["第一章", "第二章", "发展", "规划", "产业"]

        for pattern in patterns:
            print(f"\n🔍 查询模式: '{pattern}'")
            result = get_chapter_by_header(first_source, pattern)

            if "error" in result:
                print(f"   未找到")
            else:
                print(f"   ✅ 找到章节，预览:")
                lines = result.split('\n')
                for line in lines[:5]:
                    print(f"   {line}")
                print(f"   ...")

        return True

    except Exception as e:
        print(f"❌ 章节查询测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_with_agent():
    """测试与 Agent 的集成"""
    print("\n" + "="*60)
    print("测试 4: Agent 工具集成")
    print("="*60)

    try:
        from src.rag.core.tools import (
            planning_knowledge_tool,
            full_document_tool,
            chapter_context_tool,
            document_list_tool,
        )

        print("\n✅ 所有工具导入成功")
        print("\n可用的 Agent 工具:")
        print(f"  1. {planning_knowledge_tool.name}")
        print(f"     描述: {planning_knowledge_tool.description[:100]}...")
        print(f"\n  2. {full_document_tool.name}")
        print(f"     描述: {full_document_tool.description[:100]}...")
        print(f"\n  3. {chapter_context_tool.name}")
        print(f"     描述: {chapter_context_tool.description[:100]}...")
        print(f"\n  4. {document_list_tool.name}")
        print(f"     描述: {document_list_tool.description[:100]}...")

        # 测试工具调用
        print("\n🔧 测试工具调用...")
        result = document_list_tool.func("")
        print(result[:300] + "...")

        return True

    except Exception as e:
        print(f"❌ Agent 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试阶段1新功能")
    print("   全文上下文查询和文档管理")

    results = []

    # 运行所有测试
    results.append(("上下文管理器", test_context_manager()))
    results.append(("带上下文检索", test_retrieval_with_context()))
    results.append(("章节查询", test_chapter_query()))
    results.append(("Agent 工具集成", test_integration_with_agent()))

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！阶段1功能已完成。")
        print("\n✅ 下一步:")
        print("   1. 在 planning_agent.py 中使用新工具")
        print("   2. 更新 Agent 的系统提示词")
        print("   3. 测试 Agent 的复杂决策能力")
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息")


if __name__ == "__main__":
    main()

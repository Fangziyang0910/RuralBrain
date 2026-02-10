"""
RAG 知识库集成测试
测试阶段1（全文上下文）和阶段2（层次化摘要）功能
验证乡村发展规划相关问题的回答质量
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.rag.config import CHROMA_PERSIST_DIR
from src.rag.core.tools import planning_knowledge_tool
from src.rag.core.context_manager import DocumentContextManager


def test_context_manager():
    """测试阶段1：全文上下文查询"""
    print("\n" + "="*80)
    print("📚 阶段1测试：全文上下文查询")
    print("="*80)

    cm = DocumentContextManager()
    cm._ensure_loaded()  # 确保索引已加载

    # 检查索引是否已加载
    if not cm.doc_index:
        print("❌ 文档索引未找到，请先运行 src/rag/build.py 构建知识库")
        return False

    print(f"\n✅ 文档索引已加载，包含 {len(cm.doc_index)} 个文档")

    # 列出所有文档
    print("\n📋 知识库中的文档：")
    for source in cm.doc_index.keys():
        doc_info = cm.doc_index[source]
        content_length = len(doc_info.full_content) if doc_info.full_content else 0
        print(f"  • {source}")
        print(f"    - 总字符数: {content_length:,}")
        print(f"    - 文档类型: {doc_info.doc_type}")
        print(f"    - 切片数: {len(doc_info.chunks_info) if doc_info.chunks_info else 0}")

    # 测试获取完整文档
    print("\n" + "-"*80)
    print("🔍 测试1：获取完整文档")
    print("-"*80)

    policy_doc = None
    case_doc = None

    for source in cm.doc_index.keys():
        if '广州市旅游业' in source:
            policy_doc = source
        elif '罗浮' in source or '长宁' in source:
            case_doc = source

    if policy_doc:
        print(f"\n✅ 找到政策文档: {policy_doc}")
        result = cm.get_full_document(policy_doc)
        if "error" not in result:
            full_text = result.get("content", "")
            print(f"   - 文档长度: {len(full_text):,} 字符")
            print(f"   - 前200字符预览: {full_text[:200]}...")
        else:
            print(f"   ❌ 错误: {result['error']}")

    if case_doc:
        print(f"\n✅ 找到案例文档: {case_doc}")
        result = cm.get_full_document(case_doc)
        if "error" not in result:
            full_text = result.get("content", "")
            print(f"   - 文档长度: {len(full_text):,} 字符")
            print(f"   - 前200字符预览: {full_text[:200]}...")
        else:
            print(f"   ❌ 错误: {result['error']}")

    # 测试按章节查询
    print("\n" + "-"*80)
    print("🔍 测试2：章节查询")
    print("-"*80)

    if policy_doc:
        # 尝试查询包含"措施"的章节
        chapter = cm.get_chapter_by_header(policy_doc, "措施")
        if chapter:
            print(f"\n✅ 找到包含'措施'的章节:")
            print(f"   - 章节标题: {chapter.get('header', 'N/A')}")
            print(f"   - 章节内容: {chapter.get('content', '')[:200]}...")
        else:
            print("\n⚠️  未找到包含'措施'的章节（可能文档未按标题结构化）")

    return True


def test_summarization():
    """测试阶段2：层次化摘要"""
    print("\n" + "="*80)
    print("📝 阶段2测试：层次化摘要")
    print("="*80)

    cm = DocumentContextManager()
    cm._ensure_loaded()  # 确保索引已加载

    if not cm.doc_index:
        print("❌ 文档索引未找到")
        return False

    # 检查哪些文档有摘要
    docs_with_summary = []
    for source, doc_info in cm.doc_index.items():
        if doc_info.executive_summary:
            docs_with_summary.append(source)

    print(f"\n📊 摘要统计:")
    print(f"   - 总文档数: {len(cm.doc_index)}")
    print(f"   - 已生成摘要的文档: {len(docs_with_summary)}")

    if docs_with_summary:
        print(f"\n✅ 已生成摘要的文档:")
        for source in docs_with_summary:
            doc_info = cm.doc_index[source]
            print(f"\n  📄 {source}")
            print(f"     执行摘要: {doc_info.executive_summary[:150]}...")

            if doc_info.chapter_summaries:
                print(f"     章节摘要数: {len(doc_info.chapter_summaries)}")
                for i, ch in enumerate(doc_info.chapter_summaries[:3]):  # 只显示前3个
                    print(f"       {i+1}. {ch.get('title', 'N/A')[:50]}")
    else:
        print("\n⚠️  没有文档生成摘要")
        print("   提示：运行 src/rag/build.py 时选择生成摘要")

    return True


def test_knowledge_tool():
    """测试知识库检索工具"""
    print("\n" + "="*80)
    print("🔧 阶段1+2集成测试：知识库检索工具")
    print("="*80)

    # 测试问题列表（涵盖政策解读和案例参考）
    test_questions = [
        "广州市促进旅游业发展有哪些政策措施？",
        "乡村民宿高质量发展有什么指导意见？",
        "罗浮镇长宁山镇融合发展的战略重点是什么？",
        "如何构建世界级旅游目的地？",
        "文化和旅游产业专项资金如何管理？",
    ]

    print(f"\n📝 测试问题集（{len(test_questions)}个）:\n")

    results = []

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"问题 {i}/{len(test_questions)}: {question}")
        print('='*80)

        try:
            # 调用知识库检索工具
            result = planning_knowledge_tool.run(question)

            print(f"\n✅ 检索成功")

            # 分析结果（retrieve_planning_knowledge 返回字符串）
            if isinstance(result, str):
                context = result

                # 检查是否使用了policies和cases
                has_policy = any(kw in context for kw in ['政策', '措施', '办法', '通知', '广州市', '旅游'])
                has_case = any(kw in context for kw in ['案例', '罗浮', '长宁', '山城', '融合'])

                print(f"   - 返回类型: 字符串")
                print(f"   - 上下文长度: {len(context):,} 字符")
                print(f"   - 包含政策内容: {'✅' if has_policy else '❌'}")
                print(f"   - 包含案例内容: {'✅' if has_case else '❌'}")

                # 显示内容预览
                print(f"\n📋 上下文预览:")
                print(f"{'-'*80}")
                # 只显示前500字符
                preview = context[:500] + "..." if len(context) > 500 else context
                print(preview)
                print(f"{'-'*80}")

                results.append({
                    'question': question,
                    'has_policy': has_policy,
                    'has_case': has_case,
                    'context_length': len(context),
                    'success': True
                })
            else:
                print(f"⚠️  返回结果格式异常: {type(result)}")
                results.append({'question': question, 'success': False})

        except Exception as e:
            print(f"❌ 检索失败: {e}")
            import traceback
            traceback.print_exc()
            results.append({'question': question, 'success': False, 'error': str(e)})

    # 汇总结果
    print("\n" + "="*80)
    print("📊 测试结果汇总")
    print("="*80)

    success_count = sum(1 for r in results if r.get('success', False))
    policy_count = sum(1 for r in results if r.get('has_policy', False))
    case_count = sum(1 for r in results if r.get('has_case', False))

    print(f"\n✅ 成功检索: {success_count}/{len(test_questions)}")
    print(f"📄 使用政策文档: {policy_count}/{len(test_questions)}")
    print(f"📚 使用案例文档: {case_count}/{len(test_questions)}")

    # 详细结果
    print(f"\n📋 详细结果:")
    for i, r in enumerate(results, 1):
        status = "✅" if r.get('success') else "❌"
        print(f"   {i}. {status} {r['question'][:50]}...")
        if r.get('success'):
            print(f"      - 政策: {'✅' if r.get('has_policy') else '❌'}")
            print(f"      - 案例: {'✅' if r.get('has_case') else '❌'}")
            print(f"      - 上下文: {r.get('context_length', 0):,} 字符")

    return success_count == len(test_questions)


def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("🚀 RAG 知识库集成测试")
    print("="*80)
    print("\n测试目标: 验证阶段1（全文上下文）和阶段2（层次化摘要）功能")
    print("验证场景: 乡村发展规划相关问题的回答质量")
    print("数据来源: policies（政策） + cases（案例）")

    # 检查知识库是否存在
    if not CHROMA_PERSIST_DIR.exists():
        print(f"\n❌ 知识库不存在: {CHROMA_PERSIST_DIR}")
        print("   请先运行: .venv/bin/python src/rag/build.py")
        return False

    # 运行测试
    try:
        # 阶段1测试
        test1_passed = test_context_manager()

        # 阶段2测试
        test2_passed = test_summarization()

        # 集成测试
        test3_passed = test_knowledge_tool()

        # 最终结果
        print("\n" + "="*80)
        print("🎉 测试完成")
        print("="*80)

        print(f"\n阶段1（全文上下文）: {'✅ 通过' if test1_passed else '❌ 失败'}")
        print(f"阶段2（层次化摘要）: {'✅ 通过' if test2_passed else '❌ 失败'}")
        print(f"集成测试（知识检索）: {'✅ 通过' if test3_passed else '❌ 失败'}")

        if test1_passed and test2_passed and test3_passed:
            print("\n✅ 所有测试通过！知识库已准备就绪。")
            return True
        else:
            print("\n⚠️  部分测试失败，请检查上述错误信息。")
            return False

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

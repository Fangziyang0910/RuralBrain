"""
为现有知识库文档生成摘要（补充阶段2功能）
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.rag.core.context_manager import DocumentContextManager, get_context_manager
from src.rag.core.summarization import DocumentSummarizer
from src.rag.config import DEFAULT_PROVIDER
from langchain_core.documents import Document


def generate_summaries_for_existing_docs():
    """为现有知识库文档生成摘要"""

    print("="*80)
    print("为现有知识库文档生成摘要")
    print("="*80)

    # 加载上下文管理器
    cm = get_context_manager()
    cm.load()

    if not cm.doc_index:
        print("\n❌ 知识库中没有文档")
        return

    print(f"\n📚 发现 {len(cm.doc_index)} 个文档")

    # 初始化摘要生成器
    print(f"\n📝 初始化摘要生成器（模型: {DEFAULT_PROVIDER}）...")
    summarizer = DocumentSummarizer(provider=DEFAULT_PROVIDER)

    # 为每个文档生成摘要
    success_count = 0
    for source, doc_index in cm.doc_index.items():
        print(f"\n{'='*80}")
        print(f"文档 {success_count + 1}/{len(cm.doc_index)}: {source}")
        print(f"{'='*80}")

        # 检查是否已有摘要
        if doc_index.executive_summary:
            print("⏭️  该文档已有摘要，跳过")
            continue

        try:
            # 创建 Document 对象
            doc = Document(
                page_content=doc_index.full_content,
                metadata=doc_index.metadata
            )

            # 生成摘要
            summary = summarizer.generate_summary(doc)

            # 更新索引
            doc_index.executive_summary = summary.executive_summary
            doc_index.chapter_summaries = [
                {
                    "title": ch.title,
                    "level": ch.level,
                    "summary": ch.summary,
                    "key_points": ch.key_points,
                    "start_index": ch.start_index,
                    "end_index": ch.end_index
                }
                for ch in summary.chapter_summaries
            ]
            doc_index.key_points = summary.key_points

            print(f"✅ 摘要生成完成")
            print(f"   执行摘要：{len(summary.executive_summary)} 字符")
            print(f"   章节数：{len(summary.chapter_summaries)}")
            print(f"   关键要点：{len(summary.key_points)} 条")

            success_count += 1

        except Exception as e:
            print(f"❌ 摘要生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    # 保存更新后的索引
    print(f"\n{'='*80}")
    print(f"💾 保存更新后的索引...")
    cm.save()

    print(f"\n{'='*80}")
    print(f"✅ 完成！成功为 {success_count}/{len(cm.doc_index)} 个文档生成摘要")
    print(f"{'='*80}")


if __name__ == "__main__":
    generate_summaries_for_existing_docs()

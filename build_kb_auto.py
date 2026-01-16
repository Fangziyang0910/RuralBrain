"""
自动构建知识库脚本
跳过用户确认，直接构建向量数据库
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from src.rag.build import load_documents, split_documents, build_vector_store
from src.rag.core.context_manager import DocumentContextManager
from src.rag.config import CHROMA_PERSIST_DIR


def main():
    print("="*80)
    print("🚀 自动构建知识库")
    print("="*80)

    # 1. 加载文档
    print("\n📚 步骤1: 加载文档")
    documents = load_documents()
    if not documents:
        print("❌ 没有加载到文档，退出")
        return False

    # 2. 切分文档
    print("\n✂️  步骤2: 切分文档")
    splits = split_documents(documents)

    # 3. 构建向量存储
    print("\n🧠 步骤3: 构建向量数据库")
    try:
        vectorstore = build_vector_store(splits)
        print("✅ 向量数据库构建完成")
    except Exception as e:
        print(f"❌ 向量数据库构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. 构建文档索引
    print("\n📖 步骤4: 构建文档索引")
    try:
        context_manager = DocumentContextManager()
        context_manager.build_index(documents, splits)
        context_manager.save()
        print("✅ 文档索引已保存")
    except Exception as e:
        print(f"❌ 文档索引构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 跳过摘要生成（太耗时）

    # 5. 完成
    print("\n" + "="*80)
    print("🎉 知识库构建完成！")
    print("="*80)
    print(f"\n📊 统计:")
    print(f"   • 原始文档: {len(documents)} 个")
    print(f"   • 切片数量: {len(splits)} 个")
    print(f"\n💾 数据位置:")
    print(f"   • 向量数据库: {CHROMA_PERSIST_DIR}")
    print(f"   • 文档索引: {CHROMA_PERSIST_DIR / 'document_index.json'}")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

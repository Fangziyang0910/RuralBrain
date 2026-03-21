#!/usr/bin/env python3
"""
知识库构建脚本
用于从源数据构建 ChromaDB 向量数据库

用法:
    uv run python scripts/dev/build_knowledge.py
    uv run python scripts/dev/build_knowledge.py --force  # 强制重建
"""
import argparse
import shutil
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.rag.config import CHROMA_PERSIST_DIR, get_chroma_collection_metadata, get_embeddings_cached
from src.rag.utils.loaders import MarkdownLoader, TextFileLoader, PPTXLoader, DOCXLoader, DOCLoader, PDFLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.rag.core.context_manager import get_context_manager


def build_knowledge_base(force: bool = False):
    """构建知识库"""
    start = time.time()

    # 检查现有知识库
    if CHROMA_PERSIST_DIR.exists():
        if force:
            print("🗑️  清空现有知识库...")
            shutil.rmtree(CHROMA_PERSIST_DIR)
        else:
            print(f"✅ 知识库已存在: {CHROMA_PERSIST_DIR}")
            print("   使用 --force 参数强制重建")
            return

    # 加载文档
    data_dir = project_root / "src" / "data"
    all_docs = []

    print(f"\n📂 扫描目录: {data_dir}")

    supported_exts = {".md", ".txt", ".pptx", ".pdf", ".docx", ".doc"}

    for f in sorted(data_dir.rglob("*")):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext not in supported_exts:
            continue

        try:
            if ext == ".md":
                loader = MarkdownLoader(f)
            elif ext == ".txt":
                loader = TextFileLoader(f)
            elif ext == ".pptx":
                loader = PPTXLoader(f)
            elif ext == ".pdf":
                loader = PDFLoader(f)
            elif ext == ".docx":
                loader = DOCXLoader(f)
            elif ext == ".doc":
                loader = DOCLoader(f)
            else:
                continue

            docs = loader.load()
            all_docs.extend(docs)
            print(f"   ✅ {f.relative_to(data_dir)} ({len(docs)} 片段)")

        except Exception as e:
            print(f"   ⚠️  跳过 {f.name}: {e}")

    if not all_docs:
        print("\n❌ 未找到任何文档")
        sys.exit(1)

    print(f"\n📄 总文档数: {len(all_docs)}")

    # 切分
    print("✂️  文本切分中...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=500)
    splits = splitter.split_documents(all_docs)
    print(f"   切片数: {len(splits)}")

    # 向量化
    print("\n🔮 向量化中...")
    embeddings = get_embeddings_cached()

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=str(CHROMA_PERSIST_DIR),
        collection_metadata=get_chroma_collection_metadata(),
    )

    # 构建索引
    print("📝 构建文档索引...")
    cm = get_context_manager()
    cm.build_index(all_docs, splits)
    cm.save()

    duration = time.time() - start
    print(f"\n✅ 知识库构建完成!")
    print(f"   📊 文档: {len(all_docs)}, 切片: {len(splits)}")
    print(f"   ⏱️  耗时: {duration:.1f}s")
    print(f"   📁 路径: {CHROMA_PERSIST_DIR}")


def main():
    parser = argparse.ArgumentParser(description="构建知识库")
    parser.add_argument("--force", "-f", action="store_true", help="强制重建（清空现有知识库）")
    args = parser.parse_args()

    build_knowledge_base(force=args.force)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
疾病知识库构建脚本

单独构建疾病知识库，不影响规划知识库。
"""
import shutil
import sys
import time
from pathlib import Path

# UTF-8 编码设置
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.rag.config import get_embeddings_cached
from src.rag.utils.loaders import (
    MarkdownLoader, TextFileLoader, PPTXLoader,
    DOCXLoader, DOCLoader, PDFLoader
)
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.rag.core.context_manager import get_context_manager


def build_disease_knowledge(force=False):
    """构建疾病知识库"""

    # 配置
    collection_name = "diseases_knowledge"
    persist_dir = project_root / "knowledge_base" / "diseases" / "chroma_db"
    source_dirs = ["diseases"]

    print("=" * 60)
    print("疾病知识库构建")
    print("=" * 60)
    print(f"Collection: {collection_name}")
    print(f"Database: {persist_dir}")
    print(f"Sources: {', '.join(source_dirs)}")
    print()

    # 检查是否需要重建
    if persist_dir.exists() and not force:
        print(f"[SKIP] Database already exists: {persist_dir}")
        print("       Use --force to rebuild")
        return

    # 如果强制重建，删除现有数据库
    if persist_dir.exists() and force:
        print(f"[CLEAN] Removing existing database...")
        shutil.rmtree(persist_dir)

    # 加载文档
    print(f"[LOAD] Loading documents...")
    data_dir = project_root / "src" / "data"
    documents = []

    print(f"  Scanning: {data_dir}")

    for source_type in source_dirs:
        source_path = data_dir / source_type
        if not source_path.exists():
            print(f"  [WARN] Source directory not found: {source_path}")
            continue

        print(f"    Processing {source_type}/:")

        # 遍历所有子目录（牛、猪、羊等）
        for animal_dir in sorted(source_path.iterdir()):
            if not animal_dir.is_dir():
                continue

            print(f"      Processing {animal_dir.name}/:")

            # 遍历所有文件
            for file_path in sorted(animal_dir.iterdir()):
                if not file_path.is_file():
                    continue

                try:
                    # 根据文件类型选择加载器
                    if file_path.suffix.lower() == '.md':
                        loader = MarkdownLoader(file_path, category=source_type)
                    elif file_path.suffix.lower() == '.docx':
                        loader = DOCXLoader(file_path, category=source_type)
                    elif file_path.suffix.lower() == '.doc':
                        loader = DOCLoader(file_path, category=source_type)
                    elif file_path.suffix.lower() == '.pdf':
                        loader = PDFLoader(file_path, category=source_type)
                    elif file_path.suffix.lower() == '.txt':
                        loader = TextFileLoader(file_path, category=source_type)
                    elif file_path.suffix.lower() == '.pptx':
                        loader = PPTXLoader(file_path, category=source_type)
                    else:
                        print(f"      [SKIP] Unsupported format: {file_path.name}")
                        continue

                    docs = loader.load()
                    documents.extend(docs)
                    print(f"        {source_type}/{animal_dir.name}/{file_path.name} ({len(docs)} chunks)")

                except Exception as e:
                    print(f"        [ERROR] {file_path.name}: {e}")

    print(f"  [OK] Loaded {len(documents)} document chunks")

    if not documents:
        print(f"  [ERROR] No documents found")
        return

    # 分割文档
    print(f"\n  [SPLIT] Splitting documents...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )

    splits = []
    for doc in documents:
        split_docs = text_splitter.split_text(doc.page_content)
        for i, split in enumerate(split_docs):
            from langchain_core.documents import Document
            splits.append(Document(
                page_content=split,
                metadata={
                    **doc.metadata,
                    "chunk_index": i,
                }
            ))

    print(f"  [OK] Split into {len(splits)} chunks")

    # 向量化
    print(f"\n  [VECTOR] Vectorizing...")
    start_time = time.time()

    try:
        # 获取嵌入模型
        embeddings = get_embeddings_cached()

        # 创建向量数据库
        persist_dir.mkdir(parents=True, exist_ok=True)

        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=str(persist_dir),
            collection_name=collection_name,
        )

        elapsed = time.time() - start_time
        print(f"  [OK] Vector database created in {elapsed:.1f}s")
        print(f"  [INFO] Collection: {collection_name}")
        print(f"  [INFO] Chunks: {len(splits)}")
        print(f"  [INFO] Location: {persist_dir}")

    except Exception as e:
        print(f"  [ERROR] Failed to vectorize: {e}")
        import traceback
        traceback.print_exc()
        return


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="构建疾病知识库")
    parser.add_argument("--force", action="store_true", help="强制重建现有知识库")

    args = parser.parse_args()

    build_disease_knowledge(force=args.force)

    print()
    print("=" * 60)
    print("构建完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

"""
疾病知识库构建脚本

加载疾病相关文档，构建 ChromaDB 向量数据库。
支持 PDF、DOC、DOCX 等格式，markitdown 支持图片 OCR。
"""
import sys
import logging
import os
from pathlib import Path

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加 src 到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.rag.utils.loaders import load_documents_from_directory
from src.rag.config import get_embeddings_cached, CHUNK_SIZE, CHUNK_OVERLAP
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def build_disease_knowledge_base():
    """构建疾病知识库"""

    # 疾病文档目录
    diseases_dir = project_root / "knowledge_base" / "diseases" / "documents"
    chroma_dir = project_root / "knowledge_base" / "diseases" / "chroma_db"

    if not diseases_dir.exists():
        logger.error(f"疾病文档目录不存在: {diseases_dir}")
        return False

    print("=" * 60)
    print("[Disease Knowledge Base Builder]")
    print("=" * 60)
    print(f"Documents: {diseases_dir}")
    print(f"Database: {chroma_dir}")
    print()

    # Step 1: 加载文档
    print("Step 1: Loading documents...")
    try:
        documents = load_documents_from_directory(
            diseases_dir,
            file_extensions=[".pdf", ".doc", ".docx", ".txt"],
            category="diseases"
        )
        if not documents:
            logger.error("未能加载任何文档")
            return False
        print(f"[OK] Loaded {len(documents)} document chunks\n")
    except Exception as e:
        logger.error(f"加载文档失败: {e}")
        return False

    # Step 2: 分割文档
    print("Step 2: Splitting documents...")
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )

        all_splits = []
        for doc in documents:
            splits = text_splitter.split_documents([doc])
            all_splits.extend(splits)

        print(f"[OK] Split into {len(all_splits)} text chunks\n")
    except Exception as e:
        logger.error(f"分割文档失败: {e}")
        return False

    # Step 3: 获取 Embedding 模型
    print("Step 3: Loading embedding model...")
    try:
        embeddings = get_embeddings_cached()
        print(f"[OK] Embedding model loaded\n")
    except Exception as e:
        logger.error(f"加载 Embedding 模型失败: {e}")
        return False

    # Step 4: 构建向量数据库
    print("Step 4: Building vector database...")
    try:
        import chromadb
        from chromadb.config import Settings

        # 创建 ChromaDB 客户端
        chroma_dir.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(
            path=str(chroma_dir),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # 删除旧集合（如果存在）
        collection_name = "diseases_knowledge"
        try:
            client.delete_collection(collection_name)
            print(f"   Deleted old collection: {collection_name}")
        except:
            pass

        # 创建新集合
        from langchain_chroma import Chroma
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            client=client,
            persist_directory=str(chroma_dir)
        )

        # 批量添加文档（每批 5 个，适配千问 API 限制）
        batch_size = 5
        total_added = 0

        for i in range(0, len(all_splits), batch_size):
            batch = all_splits[i:i + batch_size]
            vectorstore.add_documents(batch)
            total_added += len(batch)
            print(f"   Progress: {total_added}/{len(all_splits)}")

        print(f"[OK] Vector database built with {total_added} vectors\n")
    except Exception as e:
        logger.error(f"构建向量数据库失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 完成
    print("=" * 60)
    print("[OK] Disease Knowledge Base Built Successfully!")
    print("=" * 60)
    print(f"Statistics:")
    print(f"   - Document chunks: {len(documents)}")
    print(f"   - Text chunks: {len(all_splits)}")
    print(f"   - Vectors: {total_added}")
    print(f"   - Database location: {chroma_dir}")
    print()

    return True


if __name__ == "__main__":
    success = build_disease_knowledge_base()
    sys.exit(0 if success else 1)

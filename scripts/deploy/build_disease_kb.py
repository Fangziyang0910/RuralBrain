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

# 首先尝试加载 .env 文件（需要在导入 config 之前）
try:
    from dotenv import load_dotenv
    if Path("/app/.env").exists():
        load_dotenv("/app/.env")
        print("✓ 已加载 .env 文件")
    elif Path(".env").exists():
        load_dotenv()
        print("✓ 已加载 .env 文件")
except ImportError:
    print("⚠ python-dotenv 未安装，跳过 .env 加载")

# 如果通过命令行参数传入，优先使用命令行参数（覆盖 .env 中的值）
if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        if arg.startswith("--qwen-api-key="):
            api_key = arg.split("=", 1)[1]
            os.environ["QWEN_API_KEY"] = api_key
            print(f"✓ 已通过命令行参数设置 QWEN_API_KEY")
            break

# 添加 src 到 Python 路径
# 支持本地运行和 Docker 构建：根据实际情况确定项目根目录
# 如果 /app/knowledge_base 存在，说明在 Docker 中，项目根是 /app
# 否则使用相对于脚本的路径（本地开发）
if Path("/app/knowledge_base").exists():
    project_root = Path("/app")
else:
    project_root = Path(__file__).parent.parent.parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 导入模块（现在环境变量已经设置好了）
from src.rag.utils.loaders import load_documents_from_directory
from src.rag.config import CHUNK_SIZE, CHUNK_OVERLAP, QWEN_EMBEDDING_MODEL
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 获取 embeddings - 如果通过命令行设置了密钥，直接使用 DashScope
def get_embeddings():
    """获取 Embedding 实例（构建脚本专用）"""
    # 优先使用命令行参数的密钥
    qwen_key = os.getenv("QWEN_API_KEY")
    if qwen_key:
        try:
            from langchain_community.embeddings import DashScopeEmbeddings
            import logging
            logging.info(f"使用阿里云百炼 Embedding: {QWEN_EMBEDDING_MODEL}")
            return DashScopeEmbeddings(
                model=QWEN_EMBEDDING_MODEL,
                dashscope_api_key=qwen_key
            )
        except Exception as e:
            import logging
            logging.warning(f"DashScope 初始化失败: {e}")
    # 降级到 config 中的方法
    from src.rag.config import get_embeddings_cached
    return get_embeddings_cached()

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
        embeddings = get_embeddings()
        print(f"[OK] Embedding model loaded\n")
    except Exception as e:
        logger.error(f"加载 Embedding 模型失败: {e}")
        import traceback
        traceback.print_exc()
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

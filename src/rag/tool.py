import os
from langchain_core.tools import Tool
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# 路径配置 (自动指向刚才建好的库)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "knowledge_base", "luofu_db")

# 初始化 Embeddings (避免每次调用都重新加载)
_embedding_model = None
_vectorstore = None

def get_vectorstore():
    """懒加载数据库，节省启动资源"""
    global _embedding_model, _vectorstore
    if _vectorstore is None:
        print("📥 正在加载知识库...")
        _embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
        _vectorstore = Chroma(persist_directory=DB_PATH, embedding_function=_embedding_model)
    return _vectorstore

def retrieve_planning_info(query: str) -> str:
    """
    RAG 核心检索函数
    """
    try:
        db = get_vectorstore()
        # 搜索最相关的 3 个片段
        results = db.similarity_search(query, k=3)
        
        if not results:
            return "知识库中未找到相关信息。"
            
        # 拼接结果，告诉大模型这是从哪一页查到的
        context_parts = []
        for doc in results:
            page = doc.metadata.get('page', '未知')
            context_parts.append(f"[第{page}页内容]: {doc.page_content}")
            
        return "\n\n".join(context_parts)
    except Exception as e:
        return f"查询知识库时发生错误: {str(e)}"

# ================= 定义 Agent 可用的工具 =================
# 这个变量可以直接 import 到你的 agent 代码里
planning_knowledge_tool = Tool(
    name="search_planning_strategy",
    func=retrieve_planning_info,
    description="【必须使用】当用户询问关于'博罗古城'、'长宁镇'、'罗浮山'的规划设计、战略定位、现状分析或历史文化时，使用此工具查询知识库。"
)
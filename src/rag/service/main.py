"""
Planning Service FastAPI 应用入口
提供乡村规划咨询、知识库查询等服务
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入配置
from src.rag.service.core.config import (
    SERVICE_NAME,
    SERVICE_VERSION,
    SERVICE_PORT,
    SERVICE_HOST,
    ALLOWED_ORIGINS,
    ALLOWED_METHODS,
    ALLOWED_HEADERS,
    API_PREFIX,
    LOG_LEVEL,
)

# 导入路由
from src.rag.service.api.routes import router as api_router

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== 创建 FastAPI 应用 ====================
app = FastAPI(
    title=f"{SERVICE_NAME} API",
    version=SERVICE_VERSION,
    description="""
    # 🏘️ 乡村规划咨询服务 API

    基于 RAG（检索增强生成）技术，为乡村规划提供智能咨询服务。

    ## 🎯 核心功能
    - **智能咨询**: 基于知识库的规划问答
    - **快速浏览**: 使用摘要快速了解文档核心
    - **深度分析**: 完整阅读文档进行深度理解
    - **知识检索**: 跨文档的智能检索能力
    - **流式响应**: 实时返回 AI 思考过程

    ## 📚 知识库内容
    - 博罗古城规划文档
    - 罗浮山发展战略
    - 长宁镇发展规划
    - 乡村旅游政策
    - 农业产业政策

    ## 🔬 技术架构
    - **RAG引擎**: LangChain + ChromaDB
    - **向量模型**: BAAI/bge-small-zh-v1.5
    - **LLM**: DeepSeek / GLM
    - **Agent**: LangGraph 编排

    ## 🌍 应用场景
    - **规划咨询**: 乡村发展规划咨询
    - **政策查询**: 农业政策快速查询
    - **决策支持**: 基于数据的决策建议
    - **知识管理**: 规划文档智能管理
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
)

# ==================== 配置 CORS ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
)

# ==================== 注册路由 ====================
app.include_router(api_router, prefix=API_PREFIX)

# ==================== 根路径 ====================
@app.get("/", summary="服务首页", tags=["系统"])
def root():
    """
    # 🏘️ Planning Service

    乡村规划咨询服务 API，提供智能规划咨询和知识检索能力。
    """
    return {
        "service_name": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "乡村规划咨询服务 API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "api": API_PREFIX,
        },
        "features": {
            "chat": f"{API_PREFIX}/chat/planning",
            "documents": f"{API_PREFIX}/knowledge/documents",
            "summary": f"{API_PREFIX}/knowledge/summary/{{source}}",
            "chapters": f"{API_PREFIX}/knowledge/chapters/{{source}}",
        },
    }


# ==================== 健康检查 ====================
@app.get("/health", summary="健康检查", tags=["系统"])
def health_check():
    """
    快速健康检查端点
    """
    from src.rag.config import CHROMA_PERSIST_DIR
    from pathlib import Path

    kb_loaded = Path(CHROMA_PERSIST_DIR).exists()

    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "knowledge_base_loaded": kb_loaded,
    }


# ==================== 启动事件 ====================
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} 启动中...")
    logger.info(f"服务地址: http://{SERVICE_HOST}:{SERVICE_PORT}")
    logger.info(f"API 前缀: {API_PREFIX}")
    logger.info(f"文档地址: http://{SERVICE_HOST}:{SERVICE_PORT}/docs")

    # 预加载知识库检查
    from src.rag.config import CHROMA_PERSIST_DIR
    from pathlib import Path

    if Path(CHROMA_PERSIST_DIR).exists():
        logger.info(f"知识库已加载: {CHROMA_PERSIST_DIR}")
    else:
        logger.warning(f"知识库未找到: {CHROMA_PERSIST_DIR}")

    logger.info(f"{SERVICE_NAME} 启动完成")


# ==================== 关闭事件 ====================
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info(f"{SERVICE_NAME} 正在关闭...")


# ==================== 主程序入口 ====================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.rag.service.main:app",
        host=SERVICE_HOST,
        port=SERVICE_PORT,
        reload=True,  # 开发模式：热重载
        log_level=LOG_LEVEL.lower(),
    )

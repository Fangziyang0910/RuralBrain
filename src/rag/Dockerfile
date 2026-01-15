# RAG 知识库构建 Dockerfile
# 用于在容器中构建和部署知识库
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    EMBEDDING_DEVICE=cpu \
    VECTOR_DB_TYPE=chroma

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制 uv 包管理器
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# 安装依赖
RUN uv sync --no-dev

# 创建必要的目录
RUN mkdir -p knowledge_base/chroma_db src/data

# 暴露端口（如果需要提供 Web 界面）
EXPOSE 8000

# 默认命令：构建知识库
CMD ["uv", "run", "python", "-m", "src.rag.build"]

# 使用Python 3.12官方镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 安装系统依赖（使用重试机制）
RUN apt-get update --fix-missing -o Acquire::Retries=3 -o Acquire::http::Timeout=60 && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgtk-3-0 \
    libgl1 \
    libglu1-mesa \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv 并使用项目依赖
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 复制应用代码
COPY src/algorithms/pest_detection/detector/app/ ./app/
COPY src/algorithms/pest_detection/detector/models/ ./models/
COPY src/algorithms/pest_detection/detector/run.py .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 启动命令
CMD ["uv", "run", "python", "run.py"]

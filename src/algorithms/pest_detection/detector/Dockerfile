# 使用Python 3.12官方镜像作为基础镜像 (使用国内镜像源)
FROM docker.1ms.run/library/python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 配置阿里云镜像源（Debian）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get clean

# 安装系统依赖（使用重试机制）
RUN export http_proxy= && \
    export https_proxy= && \
    export HTTP_PROXY= && \
    export HTTPS_PROXY= && \
    apt-get update --fix-missing -o Acquire::Retries=3 -o Acquire::http::Timeout=60 && \
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

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖（分步安装以提高稳定性）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings python-multipart -i https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip install --no-cache-dir numpy opencv-python-headless -i https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir ultralytics -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 复制应用代码
COPY app/ ./app/
COPY models/ ./models/
COPY run.py .

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
CMD ["python", "run.py"]
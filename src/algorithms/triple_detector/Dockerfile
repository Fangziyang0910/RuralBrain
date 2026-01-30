# RuralBrain Triple Detector Production Dockerfile
# 生产环境镜像 - 三合一检测服务
FROM python:3.12-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    YOLO_CONFIG_DIR=/app/ultralytics

# 安装系统依赖（YOLOv8 需要的依赖）
# 配置阿里云镜像源加速下载
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get clean
# 使用 cache mount 缓存 APT 下载，加速后续构建
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update --fix-missing -o Acquire::Retries=3 -o Acquire::http::Timeout=60 && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    libopencv-dev \
    python3-opencv \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv 包管理器
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 复制项目依赖配置文件
COPY pyproject.toml uv.lock ./

# 安装 Python 依赖（使用 cache mount 缓存）
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# 复制三个服务的完整代码
COPY src/algorithms/pest_detection/detector ./pest/
COPY src/algorithms/rice_detection/detector ./rice/
COPY src/algorithms/cow_detection/detector ./cow/

# 创建非root用户并设置权限
RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /app/pest/uploads /app/rice/uploads /app/cow/uploads /app/ultralytics && \
    chown -R appuser:appuser /app

USER appuser

# 复制启动脚本并转换换行符
COPY src/algorithms/triple_detector/start_all.sh .
RUN sed -i 's/\r$//' start_all.sh

# 暴露三个端口
EXPOSE 8001 8081 8002

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health && \
        curl -f http://localhost:8081/health && \
        curl -f http://localhost:8002/health || exit 1

# 启动所有服务
CMD ["bash", "start_all.sh"]

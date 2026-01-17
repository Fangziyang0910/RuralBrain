#!/bin/bash
# Planning Service 本地启动脚本（非 Docker）

set -e

echo "🏘️  启动 Planning Service..."
echo "端口: 8003"
echo "文档: http://localhost:8003/docs"
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 错误: 虚拟环境不存在，请先运行: uv sync"
    exit 1
fi

# 启动服务
echo "🚀 启动服务..."
python3 -m uvicorn src.rag.service.main:app \
    --host 0.0.0.0 \
    --port 8003 \
    --reload

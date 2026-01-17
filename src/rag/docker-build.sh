#!/bin/bash
# Planning Service Docker 构建和启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🐳 Planning Service Docker 部署"
echo "================================"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装或未在 PATH 中"
    echo "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

cd "$SCRIPT_DIR"

# 构建镜像
echo "📦 构建 Docker 镜像..."
docker build -f Dockerfile.service -t planning-service:latest "$PROJECT_ROOT"

echo ""
echo "🚀 启动服务..."
docker compose -f docker-compose.service.yml up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 10

echo ""
echo "🧪 测试服务..."
curl -s http://localhost:8003/health | python3 -m json.tool || echo "服务启动中，请稍候..."

echo ""
echo "✅ 服务已启动！"
echo ""
echo "📊 服务信息:"
echo "  - 容器名: planning-service"
echo "  - 端口: 8003"
echo "  - API 文档: http://localhost:8003/docs"
echo "  - 健康检查: http://localhost:8003/health"
echo ""
echo "📝 常用命令:"
echo "  - 查看日志: docker compose -f src/rag/docker-compose.service.yml logs -f"
echo "  - 停止服务: docker compose -f src/rag/docker-compose.service.yml down"
echo "  - 重启服务: docker compose -f src/rag/docker-compose.service.yml restart"

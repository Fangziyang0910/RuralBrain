#!/bin/bash

echo "🚀 启动 RuralBrain 开发环境..."
echo "================================"

# 检查 .env 文件
if [ ! -f ../../.env ]; then
    echo "❌ 未找到 .env 文件"
    echo "请先创建 .env 文件并填写配置"
    exit 1
fi

# 停止旧容器
echo "🛑 停止旧的开发容器..."
docker-compose -f docker-compose.dev.yml down

# 构建并启动
echo "🔨 构建开发镜像..."
docker-compose -f docker-compose.dev.yml build

echo "▶️  启动开发服务..."
docker-compose -f docker-compose.dev.yml up -d

echo "================================"
echo "✅ 开发环境启动完成！"
echo ""
echo "📍 服务地址："
echo "  - 前端:       http://localhost:3000"
echo "  - 后端 API:   http://localhost:8080/docs"
echo "  - 病虫害检测: http://localhost:8001/docs"
echo "  - 大米检测:   http://localhost:8081/docs"
echo "  - 牛只检测:   http://localhost:8002/docs"
echo "  - 规划服务:   http://localhost:8003/docs"
echo ""
echo "📝 查看日志："
echo "  docker-compose -f docker-compose.dev.yml logs -f [服务名]"
echo ""
echo "🛑 停止服务："
echo "  ./dev-stop.sh"
echo ""
echo "💡 热重载已启用，修改代码即可自动生效！"

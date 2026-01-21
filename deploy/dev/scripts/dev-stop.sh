#!/bin/bash

echo "🛑 停止 RuralBrain 开发环境..."
docker-compose -f docker-compose.dev.yml down

echo "✅ 开发环境已停止"
echo ""
echo "💡 提示：如需清理卷数据，运行："
echo "   docker-compose -f docker-compose.dev.yml down -v"

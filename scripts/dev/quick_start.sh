#!/bin/bash
# RuralBrain 快速启动脚本
# 仅启动后端主服务（用于规划和基础测试）

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  RuralBrain 快速启动${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "$PROJECT_ROOT"

# 创建 logs 目录
mkdir -p logs

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠ uv 未安装，使用系统 python${NC}"
    PYTHON_CMD="source .venv/bin/activate && python"
else
    PYTHON_CMD="uv run python"
fi

echo -e "${BLUE}启动后端主服务 (端口 8081)...${NC}"
$PYTHON_CMD service/server.py > logs/backend.log 2>&1 &
BACKEND_PID=$!

echo -e "${GREEN}✓ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
echo ""

sleep 2

if curl -s http://localhost:8081/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务就绪${NC}"
    echo ""
    echo -e "${BLUE}访问地址:${NC}"
    echo -e "  • API 文档: ${GREEN}http://localhost:8081/docs${NC}"
    echo -e "  • 后端服务: ${GREEN}http://localhost:8081${NC}"
    echo ""
    echo -e "${YELLOW}提示:${NC}"
    echo -e "  • 查看日志: tail -f logs/backend.log"
    echo -e "  • 启动前端: cd frontend/my-app && npm run dev"
    echo -e "  • 启动所有服务: bash scripts/dev/start_all_services.sh"
    echo ""
else
    echo -e "${YELLOW}⚠ 服务可能未就绪，查看日志: tail -f logs/backend.log${NC}"
fi

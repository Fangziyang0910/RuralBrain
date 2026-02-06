#!/bin/bash
# RuralBrain Docker 开发环境启动脚本
# 功能：一键启动所有服务的热重载开发环境

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================"
echo "  RuralBrain Docker 开发环境"
echo "======================================${NC}"

# 检查 Docker
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

# 进入项目根目录
cd "$(dirname "$0")/../.."

# 停止旧容器
echo -e "${YELLOW}停止旧容器...${NC}"
docker-compose -f docker/docker-compose.dev.yml down 2>/dev/null || true

# 启动开发环境
echo -e "${GREEN}启动开发环境（热重载模式）...${NC}"
docker-compose -f docker/docker-compose.dev.yml up -d --build

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
sleep 15

# 显示状态
echo -e "${GREEN}服务状态：${NC}"
docker-compose -f docker/docker-compose.dev.yml ps

echo ""
echo -e "${GREEN}======================================"
echo "  开发环境已启动"
echo "======================================${NC}"
echo ""
echo -e "${BLUE}访问地址：${NC}"
echo -e "  ${GREEN}前端:${NC}     http://localhost:3001"
echo -e "  ${GREEN}后端:${NC}     http://localhost:8081"
echo -e "  ${GREEN}后端 API:${NC} http://localhost:8081/docs"
echo -e "  ${GREEN}检测网关:${NC} http://localhost:8001"
echo -e "  ${GREEN}检测 API:${NC} http://localhost:8001/docs"
echo -e "  ${GREEN}规划服务:${NC} http://localhost:8003"
echo -e "  ${GREEN}规划 API:${NC} http://localhost:8003/docs"
echo ""
echo -e "${YELLOW}查看日志:${NC}"
echo "  docker-compose -f docker/docker-compose.dev.yml logs -f [service]"
echo ""
echo -e "${YELLOW}停止服务:${NC}"
echo "  docker-compose -f docker/docker-compose.dev.yml down"
echo ""
echo -e "${YELLOW}热重载说明:${NC}"
echo "  - 代码修改后自动重启对应服务"
echo "  - 前端：修改 frontend/ 下文件"
echo "  - 后端：修改 service/ 或 src/ 下文件"
echo "  - 检测：修改 src/algorithms/ 下文件"
echo "  - 规划：修改 src/rag/ 下文件"
echo ""

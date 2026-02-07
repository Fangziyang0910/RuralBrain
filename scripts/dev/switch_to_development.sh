#!/bin/bash
# RuralBrain 切换到开发模式脚本
# 从生产模式切换到开发模式（热重载）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  切换到开发模式（热重载）${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查生产环境是否运行
PROD_RUNNING=false
if docker compose -f docker/docker-compose.yml ps 2>/dev/null | grep -q "Up"; then
    PROD_RUNNING=true
fi

if [ "$PROD_RUNNING" = true ]; then
    echo -e "${YELLOW}检测到生产环境正在运行${NC}"
    echo ""

    read -p "是否停止生产环境并切换到开发模式？(y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}切换已取消${NC}"
        exit 0
    fi

    echo ""
    echo -e "${YELLOW}停止生产环境...${NC}"
    cd docker
    docker compose -f docker-compose.yml down
    cd "$PROJECT_ROOT"
    echo -e "${GREEN}✓ 生产环境已停止${NC}"
    echo ""
fi

# 显示将要切换到的开发环境配置
echo -e "${BLUE}开发环境配置（热重载模式）:${NC}"
echo "  - 前端 (3001): Next.js 开发模式，自动热重载"
echo "  - 后端 (8081): Uvicorn --reload，自动热重载"
echo "  - 检测 (8001): Uvicorn --reload，自动热重载"
echo "  - 规划 (8003): Uvicorn --reload，自动热重载"
echo ""
echo -e "${YELLOW}提示:${NC} 修改代码后，服务会在 1-3 秒内自动重启"
echo ""

read -p "确认启动开发环境？(y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}切换已取消${NC}"
    exit 0
fi

echo ""

# 启动开发环境
echo -e "${YELLOW}启动开发环境...${NC}"
cd docker
docker compose -f docker-compose.dev.yml up -d

echo ""
echo -e "${YELLOW}等待服务启动...${NC}"

# 等待服务健康
MAX_WAIT=120
WAIT_TIME=0

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    sleep 3
    WAIT_TIME=$((WAIT_TIME + 3))

    HEALTHY_COUNT=0
    TOTAL_COUNT=4

    if curl -s -f http://localhost:3001 > /dev/null 2>&1; then
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
    fi
    if curl -s -f http://localhost:8081/health > /dev/null 2>&1; then
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
    fi
    if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
    fi
    if curl -s -f http://localhost:8003/health > /dev/null 2>&1; then
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
    fi

    if [ $HEALTHY_COUNT -eq $TOTAL_COUNT ]; then
        break
    fi

    if [ $WAIT_TIME -eq 3 ]; then
        echo -e "  等待服务启动..."
    fi
done

cd "$PROJECT_ROOT"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ 开发环境已启动（热重载模式）${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}服务访问地址:${NC}"
echo -e "  前端:  ${GREEN}http://localhost:3001${NC}"
echo -e "  后端:  ${GREEN}http://localhost:8081/docs${NC}"
echo -e "  检测:  ${GREEN}http://localhost:8001/docs${NC}"
echo -e "  规划:  ${GREEN}http://localhost:8003/docs${NC}"
echo ""
echo -e "${BLUE}开发工作流:${NC}"
echo -e "  1. 修改代码（自动热重载 1-3 秒）"
echo -e "  2. 运行健康检查: ${YELLOW}bash scripts/dev/health_check.sh --quick${NC}"
echo -e "  3. 运行功能测试: ${YELLOW}bash scripts/dev/test_services.sh --fast${NC}"
echo ""
echo -e "${BLUE}查看日志:${NC}"
echo -e "  所有服务: ${YELLOW}cd docker && docker compose -f docker-compose.dev.yml logs -f${NC}"
echo -e "  特定服务: ${YELLOW}docker compose -f docker-compose.dev.yml logs -f <service>${NC}"
echo ""
echo -e "${BLUE}切换到生产模式:${NC}"
echo -e "  ${YELLOW}bash scripts/dev/switch_to_production.sh${NC}"
echo ""

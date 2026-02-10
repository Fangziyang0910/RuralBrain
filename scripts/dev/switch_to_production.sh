#!/bin/bash
# RuralBrain 切换到生产模式脚本
# 从开发模式（热重载）切换到生产模式

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
echo -e "${BLUE}  切换到生产模式${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查开发环境是否运行
DEV_RUNNING=false
if docker compose -f docker/docker-compose.dev.yml ps 2>/dev/null | grep -q "Up"; then
    DEV_RUNNING=true
fi

if [ "$DEV_RUNNING" = true ]; then
    echo -e "${YELLOW}检测到开发环境正在运行${NC}"
    echo ""
    echo -e "${BLUE}当前开发环境配置:${NC}"
    echo "  - 前端 (3001): 热重载模式"
    echo "  - 后端 (8081): 热重载模式"
    echo "  - 检测 (8001): 热重载模式"
    echo "  - 规划 (8003): 热重载模式"
    echo ""

    read -p "是否停止开发环境并切换到生产模式？(y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}切换已取消${NC}"
        exit 0
    fi

    echo ""
    echo -e "${YELLOW}停止开发环境...${NC}"
    cd docker
    docker compose -f docker-compose.dev.yml down
    cd "$PROJECT_ROOT"
    echo -e "${GREEN}✓ 开发环境已停止${NC}"
    echo ""
fi

# 显示将要切换到的生产环境配置
echo -e "${BLUE}生产环境配置:${NC}"
echo "  - 前端 (3001): 生产构建，无热重载"
echo "  - 后端 (8081): 生产模式，只读卷"
echo "  - 检测 (8001): 生产模式，只读卷"
echo "  - 规划 (8003): 生产模式，只读卷"
echo ""

read -p "确认启动生产环境？(y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}切换已取消${NC}"
    exit 0
fi

echo ""

# 启动生产环境
echo -e "${YELLOW}启动生产环境...${NC}"
cd docker
docker compose -f docker-compose.yml up -d

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
echo -e "${GREEN}  ✓ 生产环境已启动${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}服务访问地址:${NC}"
echo -e "  前端:  ${GREEN}http://localhost:3001${NC}"
echo -e "  后端:  ${GREEN}http://localhost:8081/docs${NC}"
echo -e "  检测:  ${GREEN}http://localhost:8001/docs${NC}"
echo -e "  规划:  ${GREEN}http://localhost:8003/docs${NC}"
echo ""
echo -e "${BLUE}常用命令:${NC}"
echo -e "  健康检查: ${YELLOW}bash scripts/dev/health_check.sh${NC}"
echo -e "  功能测试: ${YELLOW}bash scripts/dev/test_services.sh${NC}"
echo -e "  查看日志: ${YELLOW}cd docker && docker compose -f docker-compose.yml logs -f${NC}"
echo -e "  停止服务: ${YELLOW}cd docker && docker compose -f docker-compose.yml down${NC}"
echo ""
echo -e "${BLUE}切换回开发模式:${NC}"
echo -e "  ${YELLOW}bash scripts/dev/switch_to_development.sh${NC}"
echo ""

# 询问是否自动运行生产测试
read -p "是否自动运行生产环境测试？(y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    bash scripts/dev/test_production.sh
fi

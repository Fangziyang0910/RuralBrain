#!/bin/bash
# RuralBrain 生产模式功能测试脚本
# 在生产环境配置下验证所有功能

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
echo -e "${BLUE}  RuralBrain 生产环境测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查开发环境是否运行
echo -e "${YELLOW}检查当前环境...${NC}"

if docker compose -f docker/docker-compose.dev.yml ps | grep -q "Up"; then
    echo ""
    echo -e "${RED}警告: 检测到开发环境正在运行${NC}"
    echo -e "请先停止开发环境:"
    echo -e "  ${YELLOW}bash scripts/dev/stop_all_services.sh${NC}"
    echo ""
    read -p "是否自动停止开发环境并继续？(y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}停止开发环境...${NC}"
        cd docker
        docker compose -f docker-compose.dev.yml down
        cd "$PROJECT_ROOT"
        echo -e "${GREEN}开发环境已停止${NC}"
        echo ""
    else
        echo -e "${RED}测试已取消${NC}"
        exit 1
    fi
fi

# 进入 docker 目录
cd docker

# 启动生产环境
echo -e "${YELLOW}启动生产环境...${NC}"
echo ""
docker compose -f docker-compose.yml up -d

echo ""
echo -e "${YELLOW}等待服务启动...${NC}"

# 等待服务健康（最多 120 秒）
MAX_WAIT=120
WAIT_TIME=0
ALL_HEALTHY=false

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    HEALTHY_COUNT=0
    TOTAL_COUNT=4

    # 检查前端
    if curl -s -f http://localhost:3001 > /dev/null 2>&1; then
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
        if [ $WAIT_TIME -gt 5 ]; then
            echo -e "  ${GREEN}✓${NC} 前端服务 (3001)"
        fi
    fi

    # 检查后端
    if curl -s -f http://localhost:8081/health > /dev/null 2>&1; then
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
        if [ $WAIT_TIME -gt 5 ]; then
            echo -e "  ${GREEN}✓${NC} 后端服务 (8081)"
        fi
    fi

    # 检查检测服务
    if curl -s -f http://localhost:8001/health > /dev/null 2>&1; then
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
        if [ $WAIT_TIME -gt 5 ]; then
            echo -e "  ${GREEN}✓${NC} 检测服务 (8001)"
        fi
    fi

    # 检查规划服务
    if curl -s -f http://localhost:8003/health > /dev/null 2>&1; then
        HEALTHY_COUNT=$((HEALTHY_COUNT + 1))
        if [ $WAIT_TIME -gt 5 ]; then
            echo -e "  ${GREEN}✓${NC} 规划服务 (8003)"
        fi
    fi

    if [ $HEALTHY_COUNT -eq $TOTAL_COUNT ]; then
        ALL_HEALTHY=true
        break
    fi

    if [ $WAIT_TIME -eq 0 ]; then
        echo -e "  等待服务启动..."
    fi

    sleep 3
    WAIT_TIME=$((WAIT_TIME + 3))
done

echo ""

if [ "$ALL_HEALTHY" = false ]; then
    echo -e "${RED}服务启动超时${NC}"
    echo ""
    echo -e "${YELLOW}服务状态:${NC}"
    docker compose -f docker-compose.yml ps
    echo ""
    echo -e "${YELLOW}查看日志:${NC}"
    echo "  docker compose -f docker-compose.yml logs"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ 所有服务已启动${NC}"
echo ""

# 返回项目根目录
cd "$PROJECT_ROOT"

# 运行功能测试
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  运行功能测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 使用开发模式测试脚本的 normal 级别
if bash scripts/dev/test_services.sh --normal --continue; then
    TEST_RESULT=0
else
    TEST_RESULT=$?
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  生产环境验证${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 验证生产环境特定配置
echo -e "${YELLOW}验证生产环境配置...${NC}"
echo ""

# 检查容器是否使用生产镜像
echo -e "容器配置检查:"
docker compose -f docker/docker-compose.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | tail -n +2
echo ""

# 检查只读卷配置
echo -e "只读卷配置检查:"
if docker inspect ruralbrain-backend 2>/dev/null | grep -q "\"RW\": false"; then
    echo -e "  ${GREEN}✓${NC} 后端服务使用只读卷"
else
    echo -e "  ${YELLOW}⚠${NC} 后端服务未使用只读卷"
fi

# 检查健康检查配置
echo -e ""
echo -e "健康检查配置:"
if docker inspect ruralbrain-backend 2>/dev/null | grep -q "\"Health\""; then
    echo -e "  ${GREEN}✓${NC} 后端服务配置了健康检查"
else
    echo -e "  ${YELLOW}⚠${NC} 后端服务未配置健康检查"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  测试完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ 生产环境测试通过！${NC}"
    echo ""
    echo -e "${BLUE}服务访问地址:${NC}"
    echo -e "  前端: ${GREEN}http://localhost:3001${NC}"
    echo -e "  后端: ${GREEN}http://localhost:8081/docs${NC}"
    echo -e "  检测: ${GREEN}http://localhost:8001/docs${NC}"
    echo -e "  规划: ${GREEN}http://localhost:8003/docs${NC}"
    echo ""

    # 询问是否停止生产环境
    read -p "测试完成，是否停止生产环境？(y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}停止生产环境...${NC}"
        cd docker
        docker compose -f docker-compose.yml down
        echo -e "${GREEN}生产环境已停止${NC}"
    else
        echo -e "${YELLOW}生产环境继续运行${NC}"
        echo -e "停止命令: ${YELLOW}cd docker && docker compose -f docker-compose.yml down${NC}"
    fi
else
    echo -e "${RED}✗ 生产环境测试失败${NC}"
    echo ""
    echo -e "${YELLOW}查看日志:${NC}"
    echo "  cd docker && docker compose -f docker-compose.yml logs"
    echo ""
    echo -e "${YELLOW}停止生产环境:${NC}"
    echo "  cd docker && docker compose -f docker-compose.yml down"
fi

exit $TEST_RESULT

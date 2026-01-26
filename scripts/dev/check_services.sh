#!/bin/bash
# RuralBrain 服务状态检查脚本
# 检查所有服务的运行状态

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  RuralBrain 服务状态检查${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 函数：检查服务状态
check_service() {
    local NAME=$1
    local PORT=$2
    local URL=$3

    echo -e "${YELLOW}检查 $NAME (端口 $PORT)...${NC}"

    # 检查端口占用
    if lsof -ti :$PORT &>/dev/null || netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
        # 尝试访问服务
        if curl -s "$URL" > /dev/null 2>&1; then
            # 获取服务标题
            TITLE=$(curl -s "$URL" | grep -o "<title>.*</title>" | sed 's/<[^>]*>//g' | head -1)
            echo -e "  状态: ${GREEN}✓ 运行中${NC}"
            echo -e "  地址: ${GREEN}http://localhost:$PORT${NC}"
            [ -n "$TITLE" ] && echo -e "  标题: $TITLE"
        else
            echo -e "  状态: ${YELLOW}⚠ 端口被占用但无响应${NC}"
            PID=$(lsof -ti :$PORT 2>/dev/null || netstat -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1)
            echo -e "  PID: $PID"
        fi
    else
        echo -e "  状态: ${RED}✗ 未运行${NC}"
    fi
    echo ""
}

# 函数：检查进程
check_process() {
    local NAME=$1
    local PATTERN=$2

    COUNT=$(ps aux | grep -E "$PATTERN" | grep -v grep | wc -l)
    if [ $COUNT -gt 0 ]; then
        echo -e "$NAME: ${GREEN}$COUNT 个进程${NC}"
        ps aux | grep -E "$PATTERN" | grep -v grep | awk '{print "  PID:", $2, "| CMD:", $11, $12, $13}'
    else
        echo -e "$NAME: ${RED}无进程${NC}"
    fi
}

# 检查各个服务
check_service "前端服务" 3000 "http://localhost:3000"
check_service "病虫害检测服务" 8000 "http://localhost:8000/docs"
check_service "大米识别服务" 8001 "http://localhost:8001/docs"
check_service "奶牛检测服务" 8002 "http://localhost:8002/docs"
check_service "后端主服务" 8081 "http://localhost:8081/docs"

# Python 进程汇总
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "${BLUE}Python 服务进程汇总${NC}"
echo -e "${BLUE}----------------------------------------${NC}"
check_process "后端服务" "service/server.py"
check_process "病虫害检测" "pest_detection.*start_service"
check_process "大米识别" "rice_detection.*start_service"
check_process "奶牛检测" "cow_detection.*start_service"
echo ""

# 端口占用汇总
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "${BLUE}端口占用情况${NC}"
echo -e "${BLUE}----------------------------------------${NC}"

for PORT in 3000 8000 8001 8002 8081; do
    if lsof -ti :$PORT &>/dev/null || netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
        PID=$(lsof -ti :$PORT 2>/dev/null || netstat -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1)
        CMD=$(ps -p $PID -o comm= 2>/dev/null || echo "unknown")
        echo -e "端口 $PORT: ${GREEN}占用${NC} (PID: $PID, $CMD)"
    else
        echo -e "端口 $PORT: ${RED}空闲${NC}"
    fi
done
echo ""

# 服务健康建议
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "${BLUE}健康建议${NC}"
echo -e "${BLUE}----------------------------------------${NC}"

# 统计运行服务数量
RUNNING_COUNT=0
for PORT in 3000 8000 8001 8002 8081; do
    if lsof -ti :$PORT &>/dev/null || netstat -tlnp 2>/dev/null | grep -q ":$PORT "; then
        ((RUNNING_COUNT++))
    fi
done

if [ $RUNNING_COUNT -eq 5 ]; then
    echo -e "${GREEN}✓ 所有服务运行正常${NC}"
elif [ $RUNNING_COUNT -ge 2 ]; then
    echo -e "${YELLOW}⚠ 部分服务未运行 ($RUNNING_COUNT/5)${NC}"
    echo -e "  建议: 运行 bash scripts/dev/start_all_services.sh"
else
    echo -e "${RED}✗ 多数服务未运行 ($RUNNING_COUNT/5)${NC}"
    echo -e "  建议: 运行 bash scripts/dev/start_all_services.sh"
fi

echo ""
echo -e "${BLUE}========================================${NC}"

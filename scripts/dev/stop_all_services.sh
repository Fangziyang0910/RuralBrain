#!/bin/bash
# RuralBrain 服务停止脚本
# 停止所有运行中的服务

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  RuralBrain 服务停止脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 函数：停止指定端口的进程
stop_service_on_port() {
    local PORT=$1
    local SERVICE_NAME=$2

    # 查找占用端口的进程
    PID=$(lsof -ti :$PORT 2>/dev/null || netstat -tlnp 2>/dev/null | grep :$PORT | awk '{print $7}' | cut -d'/' -f1)

    if [ -n "$PID" ]; then
        echo -e "${YELLOW}停止 $SERVICE_NAME (端口 $PORT, PID: $PID)...${NC}"
        kill -15 $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        sleep 1

        # 检查是否已停止
        if lsof -ti :$PORT &>/dev/null; then
            echo -e "${RED}✗ $SERVICE_NAME 停止失败${NC}"
        else
            echo -e "${GREEN}✓ $SERVICE_NAME 已停止${NC}"
        fi
    else
        echo -e "${YELLOW}○ $SERVICE_NAME 未运行${NC}"
    fi
}

# 函数：停止指定名称的 Python 进程
stop_python_service() {
    local SERVICE_NAME=$1
    local PATTERN=$2

    PIDS=$(ps aux | grep -E "python.*$PATTERN" | grep -v grep | awk '{print $2}')

    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}停止 $SERVICE_NAME...${NC}"
        for PID in $PIDS; do
            kill -15 $PID 2>/dev/null
        done
        sleep 1

        # 检查是否还有进程
        REMAINING=$(ps aux | grep -E "python.*$PATTERN" | grep -v grep | wc -l)
        if [ "$REMAINING" -gt 0 ]; then
            echo -e "${YELLOW}强制停止 $SERVICE_NAME...${NC}"
            ps aux | grep -E "python.*$PATTERN" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
        fi
        echo -e "${GREEN}✓ $SERVICE_NAME 已停止${NC}"
    else
        echo -e "${YELLOW}○ $SERVICE_NAME 未运行${NC}"
    fi
}

# 按顺序停止服务
echo -e "${BLUE}停止所有服务...${NC}"
echo ""

# 停止前端服务
echo -e "[1/5] 停止前端服务..."
stop_service_on_port 3000 "前端服务"

# 停止后端服务
echo -e "[2/5] 停止后端主服务..."
stop_service_on_port 8081 "后端主服务"
stop_python_service "后端主服务（Python）" "service/server.py"

# 停止检测服务
echo -e "[3/5] 停止病虫害检测服务..."
stop_service_on_port 8000 "病虫害检测服务"
stop_python_service "病虫害检测服务" "pest_detection"

echo -e "[4/5] 停止大米识别服务..."
stop_service_on_port 8001 "大米识别服务"
stop_python_service "大米识别服务" "rice_detection"

echo -e "[5/5] 停止奶牛检测服务..."
stop_service_on_port 8002 "奶牛检测服务"
stop_python_service "奶牛检测服务" "cow_detection"

# 清理可能的僵尸进程
echo ""
echo -e "${YELLOW}清理僵尸进程...${NC}"
pkill -f "python.*start_service.py" 2>/dev/null && echo -e "${GREEN}✓ 已清理僵尸服务进程${NC}" || echo -e "${YELLOW}○ 无僵尸进程${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  所有服务已停止${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

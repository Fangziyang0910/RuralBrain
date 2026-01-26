#!/bin/bash
# RuralBrain 服务启动脚本
# 一键启动所有核心服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  RuralBrain 服务启动脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查必要的命令
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ 错误: $1 未安装${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}检查环境...${NC}"
check_command python3
check_command npm

# 检查 uv
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠ 警告: uv 未安装，将使用系统 python${NC}"
    USE_UV=false
else
    USE_UV=true
fi

# 进入项目根目录
cd "$PROJECT_ROOT"

# 创建 logs 目录
mkdir -p logs

# Python 运行函数
run_python() {
    if [ "$USE_UV" = true ]; then
        uv run python "$@"
    else
        source .venv/bin/activate
        python "$@"
    fi
}

# ========================================
# 启动检测服务
# ========================================
echo ""
echo -e "${BLUE}[1/4] 启动病虫害检测服务 (端口 8000)...${NC}"

cd "$PROJECT_ROOT/src/algorithms/pest_detection/detector"
run_python start_service.py > "$PROJECT_ROOT/logs/pest_detection.log" 2>&1 &
PEST_PID=$!
echo -e "${GREEN}✓ 病虫害检测服务已启动 (PID: $PEST_PID)${NC}"

echo -e "${YELLOW}等待服务启动...${NC}"
sleep 3

if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 病虫害检测服务就绪 (http://localhost:8000)${NC}"
else
    echo -e "${YELLOW}⚠ 警告: 病虫害检测服务可能未正常启动，查看日志: logs/pest_detection.log${NC}"
fi

# ========================================
echo ""
echo -e "${BLUE}[2/4] 启动大米识别服务 (端口 8001)...${NC}"

cd "$PROJECT_ROOT/src/algorithms/rice_detection/detector"
run_python start_service.py > "$PROJECT_ROOT/logs/rice_detection.log" 2>&1 &
RICE_PID=$!
echo -e "${GREEN}✓ 大米识别服务已启动 (PID: $RICE_PID)${NC}"

echo -e "${YELLOW}等待服务启动...${NC}"
sleep 3

if curl -s http://localhost:8001/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 大米识别服务就绪 (http://localhost:8001)${NC}"
else
    echo -e "${YELLOW}⚠ 警告: 大米识别服务可能未正常启动，查看日志: logs/rice_detection.log${NC}"
fi

# ========================================
echo ""
echo -e "${BLUE}[3/4] 启动奶牛检测服务 (端口 8002)...${NC}"

cd "$PROJECT_ROOT/src/algorithms/cow_detection/detector"
run_python start_service.py > "$PROJECT_ROOT/logs/cow_detection.log" 2>&1 &
COW_PID=$!
echo -e "${GREEN}✓ 奶牛检测服务已启动 (PID: $COW_PID)${NC}"

echo -e "${YELLOW}等待服务启动...${NC}"
sleep 3

if curl -s http://localhost:8002/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 奶牛检测服务就绪 (http://localhost:8002)${NC}"
else
    echo -e "${YELLOW}⚠ 警告: 奶牛检测服务可能未正常启动，查看日志: logs/cow_detection.log${NC}"
fi

# ========================================
echo ""
echo -e "${BLUE}[4/4] 启动后端主服务 (端口 8081)...${NC}"

cd "$PROJECT_ROOT"
run_python service/server.py > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ 后端主服务已启动 (PID: $BACKEND_PID)${NC}"

echo -e "${YELLOW}等待服务启动...${NC}"
sleep 3

if curl -s http://localhost:8081/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端主服务就绪 (http://localhost:8081)${NC}"
else
    echo -e "${YELLOW}⚠ 警告: 后端主服务可能未正常启动，查看日志: logs/backend.log${NC}"
fi

# ========================================
# 启动前端服务（可选）
# ========================================
echo ""
echo -e "${YELLOW}是否启动前端服务？(y/n) [建议手动启动以便查看日志]${NC}"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo -e "${BLUE}启动前端服务 (端口 3000)...${NC}"

    cd "$PROJECT_ROOT/frontend/my-app"

    # 检查 node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}首次运行，安装依赖...${NC}"
        npm install
    fi

    npm run dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo -e "${GREEN}✓ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"

    echo -e "${YELLOW}等待服务启动...${NC}"
    sleep 5

    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 前端服务就绪 (http://localhost:3000)${NC}"
    else
        echo -e "${YELLOW}⚠ 警告: 前端服务可能未正常启动，查看日志: logs/frontend.log${NC}"
    fi
else
    echo -e "${YELLOW}跳过前端服务启动${NC}"
    echo -e "${YELLOW}手动启动命令: cd frontend/my-app && npm run dev${NC}"
fi

# ========================================
# 启动完成
# ========================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  服务启动完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}服务状态:${NC}"
echo -e "  • 病虫害检测: ${GREEN}http://localhost:8000${NC}/docs"
echo -e "  • 大米识别:   ${GREEN}http://localhost:8001${NC}/docs"
echo -e "  • 奶牛检测:   ${GREEN}http://localhost:8002${NC}/docs"
echo -e "  • 后端服务:   ${GREEN}http://localhost:8081${NC}/docs"
echo -e "  • 前端界面:   ${GREEN}http://localhost:3000${NC}"
echo ""
echo -e "${YELLOW}提示:${NC}"
echo -e "  • 查看日志: tail -f logs/*.log"
echo -e "  • 停止服务: bash scripts/dev/stop_all_services.sh"
echo -e "  • 检查状态: bash scripts/dev/check_services.sh"
echo ""

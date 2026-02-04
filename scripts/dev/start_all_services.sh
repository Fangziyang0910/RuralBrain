#!/bin/bash
# RuralBrain 服务启动脚本 (macOS/Linux)
# 一键启动所有核心服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 参数解析
NO_DETECTION=false
NO_PLANNING=false
NO_FRONTEND=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-detection)
            NO_DETECTION=true
            shift
            ;;
        --no-planning)
            NO_PLANNING=true
            shift
            ;;
        --no-frontend)
            NO_FRONTEND=true
            shift
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            exit 1
            ;;
    esac
done

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
    echo -e "${YELLOW}⚠ 警告: uv 未安装，将使用虚拟环境中的 Python${NC}"
    USE_UV=false

    # 检查虚拟环境
    if [ ! -d "$PROJECT_ROOT/.venv" ]; then
        echo -e "${RED}✗ 错误: 虚拟环境不存在，请先运行: uv sync${NC}"
        exit 1
    fi
else
    USE_UV=true
    echo -e "${GREEN}✓ uv 已安装${NC}"
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
        source "$PROJECT_ROOT/.venv/bin/activate"
        python "$@"
    fi
}

# ========================================
# 启动检测服务网关 (端口 8001)
# ========================================
if [ "$NO_DETECTION" = false ]; then
    echo ""
    echo -e "${BLUE}[1/4] 启动检测服务网关 (端口 8001)...${NC}"

    run_python src/algorithms/api/main.py > "$PROJECT_ROOT/logs/detection.log" 2>&1 &
    DETECTION_PID=$!
    echo -e "${GREEN}✓ 检测服务网关已启动 (PID: $DETECTION_PID)${NC}"

    echo -e "${YELLOW}等待服务启动...${NC}"
    sleep 3

    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 检测服务网关就绪 (http://localhost:8001)${NC}"
    else
        echo -e "${YELLOW}⚠ 警告: 检测服务网关可能未正常启动，查看日志: logs/detection.log${NC}"
    fi
else
    echo -e "${YELLOW}[1/4] 跳过检测服务网关${NC}"
fi

# ========================================
# 启动规划咨询服务 (端口 8003)
# ========================================
if [ "$NO_PLANNING" = false ]; then
    echo ""
    echo -e "${BLUE}[2/4] 启动规划咨询服务 (端口 8003)...${NC}"

    run_python src/rag/service/main.py > "$PROJECT_ROOT/logs/planning.log" 2>&1 &
    PLANNING_PID=$!
    echo -e "${GREEN}✓ 规划咨询服务已启动 (PID: $PLANNING_PID)${NC}"

    echo -e "${YELLOW}等待服务启动...${NC}"
    sleep 3

    if curl -s http://localhost:8003/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 规划咨询服务就绪 (http://localhost:8003)${NC}"
    else
        echo -e "${YELLOW}⚠ 警告: 规划咨询服务可能未正常启动，查看日志: logs/planning.log${NC}"
    fi
else
    echo -e "${YELLOW}[2/4] 跳过规划咨询服务${NC}"
fi

# ========================================
# 启动后端主服务 (端口 8081)
# ========================================
echo ""
echo -e "${BLUE}[3/4] 启动后端主服务 (端口 8081)...${NC}"

run_python run_server.py > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
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
# 启动前端服务 (端口 3001)
# ========================================
if [ "$NO_FRONTEND" = false ]; then
    echo ""
    echo -e "${BLUE}[4/4] 启动前端服务 (端口 3001)...${NC}"

    cd "$PROJECT_ROOT/frontend"

    # 检查 node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}首次运行，安装依赖...${NC}"
        npm install
    fi

    # 启动前端（推荐在单独的终端手动启动以查看日志）
    echo -e "${YELLOW}提示: 建议在单独的终端手动启动前端以查看日志${NC}"
    echo -e "${YELLOW}      命令: cd frontend && npm run dev${NC}"
    echo ""
    read -p "是否现在启动前端？(y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_ROOT"
        if [ "$USE_UV" = true ]; then
            uv run python run_frontend.py > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
        else
            source "$PROJECT_ROOT/.venv/bin/activate"
            python run_frontend.py > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
        fi
        FRONTEND_PID=$!
        echo -e "${GREEN}✓ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"

        echo -e "${YELLOW}等待服务启动...${NC}"
        sleep 5

        if curl -s http://localhost:3001 > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 前端服务就绪 (http://localhost:3001)${NC}"
        else
            echo -e "${YELLOW}⚠ 警告: 前端服务可能未正常启动，查看日志: logs/frontend.log${NC}"
        fi
    else
        echo -e "${YELLOW}跳过前端服务启动${NC}"
        echo -e "${YELLOW}手动启动命令: cd frontend && npm run dev${NC}"
    fi
else
    echo -e "${YELLOW}[4/4] 跳过前端服务${NC}"
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
if [ "$NO_DETECTION" = false ]; then
    echo -e "  • 检测服务网关: ${GREEN}http://localhost:8001${NC}/docs"
fi
if [ "$NO_PLANNING" = false ]; then
    echo -e "  • 规划咨询服务: ${GREEN}http://localhost:8003${NC}/docs"
fi
echo -e "  • 后端主服务:   ${GREEN}http://localhost:8081${NC}/docs"
if [ "$NO_FRONTEND" = false ]; then
    echo -e "  • 前端界面:     ${GREEN}http://localhost:3001${NC}"
fi
echo ""
echo -e "${BLUE}提示:${NC}"
echo -e "  • 查看日志: ${YELLOW}tail -f logs/*.log${NC}"
echo -e "  • 停止服务: ${YELLOW}bash scripts/dev/stop_all_services.sh${NC}"
echo -e "  • 检查状态: ${YELLOW}bash scripts/dev/check_services.sh${NC}"
echo ""

#!/bin/bash
# RuralBrain Docker 服务启动脚本
# 使用 Docker Compose 热重载模式启动所有服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 参数解析
DETACH=false
BUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--detach)
            DETACH=true
            shift
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -d, --detach    后台运行"
            echo "  -b, --build     重新构建镜像"
            echo "  -h, --help      显示帮助信息"
            exit 0
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            exit 1
            ;;
    esac
done

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  RuralBrain Docker 开发环境${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    exit 1
fi

# 检查 Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装${NC}"
    exit 1
fi

# 进入 docker 目录
cd docker

# 构建镜像（如果需要）
if [ "$BUILD" = true ]; then
    echo -e "${YELLOW}构建 Docker 镜像...${NC}"
    docker compose -f docker-compose.dev.yml build
    echo ""
fi

# 启动服务
echo -e "${YELLOW}启动服务（热重载模式）...${NC}"
echo ""

if [ "$DETACH" = true ]; then
    docker compose -f docker-compose.dev.yml up -d
    echo ""
    echo -e "${GREEN}服务已在后台启动${NC}"
    echo ""
    echo -e "${BLUE}服务状态:${NC}"
    docker compose -f docker-compose.dev.yml ps
    echo ""
    echo -e "${BLUE}查看日志:${NC}"
    echo "  docker compose -f docker-compose.dev.yml logs -f"
    echo ""
    echo -e "${BLUE}停止服务:${NC}"
    echo "  docker compose -f docker-compose.dev.yml down"
else
    echo -e "${YELLOW}提示: 使用 Ctrl+C 停止服务${NC}"
    echo ""
    docker compose -f docker-compose.dev.yml up
fi

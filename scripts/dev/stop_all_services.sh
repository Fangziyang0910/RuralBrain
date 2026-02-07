#!/bin/bash
# RuralBrain Docker 服务停止脚本
# 使用 Docker Compose 停止所有服务

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 参数解析
VOLUMES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--volumes)
            VOLUMES=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -v, --volumes   同时删除数据卷"
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
cd "$PROJECT_ROOT/docker"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  停止 RuralBrain 服务${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装${NC}"
    exit 1
fi

# 停止服务
echo -e "${YELLOW}停止服务...${NC}"
docker compose -f docker-compose.dev.yml down

# 删除卷（如果需要）
if [ "$VOLUMES" = true ]; then
    echo ""
    echo -e "${YELLOW}删除数据卷...${NC}"
    docker compose -f docker-compose.dev.yml down -v
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  服务已停止${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

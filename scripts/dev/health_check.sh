#!/bin/bash
# RuralBrain 服务健康检查脚本
# 检查所有服务的健康状态和连通性

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 默认参数
QUICK=false
VERBOSE=false
SPECIFIC_SERVICE=""
EXIT_CODE=0

# 帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --quick            快速检查模式（仅检查健康端点）"
    echo "  --verbose          显示详细输出"
    echo "  --service <name>   仅检查指定服务 (frontend|backend|detection|planning)"
    echo "  -h, --help         显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                              # 完整健康检查"
    echo "  $0 --quick                      # 快速检查"
    echo "  $0 --service backend            # 仅检查后端服务"
    echo "  $0 --verbose                    # 详细输出"
}

# 参数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --service)
            SPECIFIC_SERVICE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  RuralBrain 服务健康检查${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 超时设置（秒）
TIMEOUT=10

# 函数：检查 HTTP 端点
check_http_endpoint() {
    local NAME=$1
    local URL=$2
    local EXPECTED=${3:-200}

    if [ "$VERBOSE" = true ]; then
        echo -e "${YELLOW}检查 $NAME${NC}"
        echo -e "  URL: $URL"
    fi

    # 使用 curl 检查
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$URL" 2>/dev/null || echo "000")

    if [ "$RESPONSE" = "$EXPECTED" ]; then
        echo -e "$NAME: ${GREEN}✓ 健康${NC} (HTTP $RESPONSE)"
        if [ "$VERBOSE" = true ]; then
            curl -s --max-time $TIMEOUT "$URL" 2>/dev/null | jq '.' 2>/dev/null || curl -s --max-time $TIMEOUT "$URL" 2>/dev/null
            echo ""
        fi
        return 0
    else
        echo -e "$NAME: ${RED}✗ 不健康${NC} (HTTP $RESPONSE, 期望 $EXPECTED)"
        EXIT_CODE=1
        return 1
    fi
}

# 函数：检查服务容器状态
check_container_status() {
    local CONTAINER_NAME=$1

    if ! command -v docker &> /dev/null; then
        return 0
    fi

    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        if [ "$VERBOSE" = true ]; then
            local STATUS=$(docker inspect --format='{{.State.Status}}' $CONTAINER_NAME 2>/dev/null)
            local HEALTH=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "no-healthcheck")
            echo -e "  容器状态: ${GREEN}$STATUS${NC} ($HEALTH)"
        fi
        return 0
    else
        echo -e "  容器状态: ${YELLOW}未运行${NC}"
        return 1
    fi
}

# 函数：检查前端服务
check_frontend() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}前端服务 (端口 3001)${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 检查容器
    check_container_status "ruralbrain-frontend" 2>/dev/null || true

    # 检查 HTTP 响应
    check_http_endpoint "前端" "http://localhost:3001" "200"

    if [ "$QUICK" = false ]; then
        # 检查静态资源
        echo -e ""
        echo -e "静态资源检查:"
        if curl -s --head "http://localhost:3001/_next/static" --max-time $TIMEOUT | grep -q "HTTP"; then
            echo -e "  静态资源: ${GREEN}✓ 可访问${NC}"
        else
            echo -e "  静态资源: ${YELLOW}⚠ 可能未构建${NC}"
        fi
    fi
    echo ""
}

# 函数：检查后端服务
check_backend() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}后端主服务 (端口 8081)${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 检查容器
    check_container_status "ruralbrain-backend" 2>/dev/null || true

    # 检查健康端点
    check_http_endpoint "后端健康" "http://localhost:8081/health" "200"

    # 检查 API 文档
    if [ "$QUICK" = false ]; then
        check_http_endpoint "API 文档" "http://localhost:8081/docs" "200"
    fi
    echo ""
}

# 函数：检查检测服务
check_detection() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}检测服务网关 (端口 8001)${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 检查容器
    check_container_status "ruralbrain-detection-service" 2>/dev/null || \
    check_container_status "ruralbrain-detection-service-dev" 2>/dev/null || true

    # 检查健康端点
    check_http_endpoint "检测服务健康" "http://localhost:8001/health" "200"

    if [ "$QUICK" = false ]; then
        # 检查各个检测端点
        echo -e ""
        echo -e "检测端点检查:"
        check_http_endpoint "  病虫害检测" "http://localhost:8001/detection/pest/docs" "200" 2>/dev/null || \
            echo -e "  病虫害检测: ${YELLOW}⚠ 文档端点未响应${NC}"

        check_http_endpoint "  大米识别" "http://localhost:8001/detection/rice/docs" "200" 2>/dev/null || \
            echo -e "  大米识别: ${YELLOW}⚠ 文档端点未响应${NC}"

        check_http_endpoint "  奶牛检测" "http://localhost:8001/detection/cow/docs" "200" 2>/dev/null || \
            echo -e "  奶牛检测: ${YELLOW}⚠ 文档端点未响应${NC}"
    fi
    echo ""
}

# 函数：检查规划服务
check_planning() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}规划咨询服务 (端口 8003)${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 检查容器
    check_container_status "ruralbrain-planning-service" 2>/dev/null || \
    check_container_status "ruralbrain-planning-service-dev" 2>/dev/null || true

    # 检查健康端点
    check_http_endpoint "规划服务健康" "http://localhost:8003/health" "200"

    if [ "$QUICK" = false ]; then
        # 检查 API 文档
        check_http_endpoint "API 文档" "http://localhost:8003/docs" "200"
    fi
    echo ""
}

# 函数：检查服务间连通性
check_connectivity() {
    if [ "$QUICK" = true ]; then
        return
    fi

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}服务间连通性检查${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 检查后端是否能访问检测服务
    if docker exec ruralbrain-backend curl -s -f http://detection-service:8001/health > /dev/null 2>&1; then
        echo -e "后端 → 检测服务: ${GREEN}✓ 连通${NC}"
    else
        echo -e "后端 → 检测服务: ${YELLOW}⚠ 未连通${NC}"
    fi

    # 检查后端是否能访问规划服务
    if docker exec ruralbrain-backend curl -s -f http://planning-service:8003/health > /dev/null 2>&1; then
        echo -e "后端 → 规划服务: ${GREEN}✓ 连通${NC}"
    else
        echo -e "后端 → 规划服务: ${YELLOW}⚠ 未连通${NC}"
    fi

    echo ""
}

# 主逻辑
if [ -n "$SPECIFIC_SERVICE" ]; then
    case $SPECIFIC_SERVICE in
        frontend)
            check_frontend
            ;;
        backend)
            check_backend
            ;;
        detection)
            check_detection
            ;;
        planning)
            check_planning
            ;;
        *)
            echo -e "${RED}错误: 未知服务 '$SPECIFIC_SERVICE'${NC}"
            echo -e "可用服务: frontend, backend, detection, planning"
            exit 1
            ;;
    esac
else
    # 检查所有服务
    check_frontend
    check_backend
    check_detection
    check_planning

    # 服务间连通性检查
    check_connectivity
fi

# 摘要
echo -e "${BLUE}========================================${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ 所有服务健康${NC}"
else
    echo -e "${RED}✗ 部分服务不健康${NC}"
fi
echo -e "${BLUE}========================================${NC}"

exit $EXIT_CODE

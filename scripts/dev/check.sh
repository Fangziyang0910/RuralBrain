#!/bin/bash
# RuralBrain 服务检查脚本
# 统一的健康检查和功能测试入口

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 默认参数
MODE="health"
TEST_LEVEL="normal"
VERBOSE=false
SPECIFIC_SERVICE=""
CONTINUE_ON_ERROR=false
EXIT_CODE=0
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RESOURCES_DIR="$PROJECT_ROOT/tests/resources"

# 服务 URL
FRONTEND_URL="http://localhost:3001"
BACKEND_URL="http://localhost:8081"
DETECTION_URL="http://localhost:8001"
PLANNING_URL="http://localhost:8003"

# 帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "模式:"
    echo "  --health           健康检查模式（检查服务状态，默认）"
    echo "  --test [level]     功能测试模式 (fast|normal|full)"
    echo ""
    echo "选项:"
    echo "  --quick            快速检查（仅健康端点，同 --test fast）"
    echo "  --verbose          显示详细输出"
    echo "  --continue         测试失败时继续（仅测试模式）"
    echo "  --service <name>   仅检查指定服务 (frontend|backend|detection|planning)"
    echo "  -h, --help         显示帮助信息"
    echo ""
    echo "测试级别说明:"
    echo "  fast  : 基础连通性 + 健康检查 (< 30秒)"
    echo "  normal: fast + 检测服务功能测试 (< 2分钟) [默认]"
    echo "  full  : normal + Agent/规划/前端测试 (< 5分钟)"
    echo ""
    echo "示例:"
    echo "  $0 --health                    # 健康检查"
    echo "  $0 --test fast                 # 快速功能测试"
    echo "  $0 --quick                     # 快速检查（别名）"
    echo "  $0 --test full                 # 完整功能测试"
    echo "  $0 --service backend           # 仅检查后端"
}

# 参数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --health)
            MODE="health"
            shift
            ;;
        --test)
            MODE="test"
            if [[ "$2" =~ ^(fast|normal|full)$ ]]; then
                TEST_LEVEL="$2"
                shift 2
            else
                TEST_LEVEL="normal"
                shift
            fi
            ;;
        --quick)
            MODE="test"
            TEST_LEVEL="fast"
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --continue)
            CONTINUE_ON_ERROR=true
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
cd "$PROJECT_ROOT"

# 超时设置
TIMEOUT=10

# ===== 通用函数 =====

# 函数：检查 HTTP 端点
check_http() {
    local NAME=$1
    local URL=$2
    local EXPECTED=${3:-200}

    if [ "$VERBOSE" = true ]; then
        echo -e "  检查: $NAME"
        echo -e "  URL: $URL"
    fi

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

# 函数：检查容器状态
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

# ===== 健康检查模式 =====

check_service_health() {
    local SERVICE=$1

    case $SERVICE in
        frontend)
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${YELLOW}前端服务 (端口 3001)${NC}"
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            check_container_status "ruralbrain-frontend" 2>/dev/null || true
            check_http "前端" "$FRONTEND_URL" "200"
            if [ "$VERBOSE" = true ]; then
                echo -e ""
                echo -e "静态资源检查:"
                if curl -s --head "$FRONTEND_URL/_next/static" --max-time $TIMEOUT | grep -q "HTTP"; then
                    echo -e "  静态资源: ${GREEN}✓ 可访问${NC}"
                else
                    echo -e "  静态资源: ${YELLOW}⚠ 可能未构建${NC}"
                fi
            fi
            echo ""
            ;;
        backend)
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${YELLOW}后端主服务 (端口 8081)${NC}"
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            check_container_status "ruralbrain-backend" 2>/dev/null || true
            check_http "后端健康" "$BACKEND_URL/health" "200"
            if [ "$VERBOSE" = true ]; then
                check_http "API 文档" "$BACKEND_URL/docs" "200"
            fi
            echo ""
            ;;
        detection)
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${YELLOW}检测服务网关 (端口 8001)${NC}"
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            check_container_status "ruralbrain-detection-service" 2>/dev/null || \
            check_container_status "ruralbrain-detection-service-dev" 2>/dev/null || true
            check_http "检测服务健康" "$DETECTION_URL/health" "200"
            if [ "$VERBOSE" = true ]; then
                echo -e ""
                echo -e "检测端点检查:"
                check_http "  病虫害检测" "$DETECTION_URL/detection/pest/docs" "200" 2>/dev/null || \
                    echo -e "  病虫害检测: ${YELLOW}⚠ 文档端点未响应${NC}"
                check_http "  大米识别" "$DETECTION_URL/detection/rice/docs" "200" 2>/dev/null || \
                    echo -e "  大米识别: ${YELLOW}⚠ 文档端点未响应${NC}"
                check_http "  奶牛检测" "$DETECTION_URL/detection/cow/docs" "200" 2>/dev/null || \
                    echo -e "  奶牛检测: ${YELLOW}⚠ 文档端点未响应${NC}"
            fi
            echo ""
            ;;
        planning)
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${YELLOW}规划咨询服务 (端口 8003)${NC}"
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            check_container_status "ruralbrain-planning-service" 2>/dev/null || \
            check_container_status "ruralbrain-planning-service-dev" 2>/dev/null || true
            check_http "规划服务健康" "$PLANNING_URL/health" "200"
            if [ "$VERBOSE" = true ]; then
                check_http "API 文档" "$PLANNING_URL/docs" "200"
            fi
            echo ""
            ;;
    esac
}

check_connectivity() {
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

run_health_check() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  RuralBrain 服务健康检查${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    if [ -n "$SPECIFIC_SERVICE" ]; then
        check_service_health "$SPECIFIC_SERVICE"
    else
        check_service_health "frontend"
        check_service_health "backend"
        check_service_health "detection"
        check_service_health "planning"
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
}

# ===== 功能测试模式 =====

# 函数：运行测试
run_test() {
    local TEST_NAME=$1
    local TEST_FUNC=$2
    local LEVEL=$3

    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    # 检查是否应该运行此测试
    case $LEVEL in
        fast)
            # 所有级别都运行
            ;;
        normal)
            if [ "$TEST_LEVEL" = "fast" ]; then
                return
            fi
            ;;
        full)
            if [ "$TEST_LEVEL" = "fast" ] || [ "$TEST_LEVEL" = "normal" ]; then
                return
            fi
            ;;
    esac

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}$TEST_NAME${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if $TEST_FUNC; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}✓ $TEST_NAME 通过${NC}"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        EXIT_CODE=1
        echo -e "${RED}✗ $TEST_NAME 失败${NC}"
        if [ "$CONTINUE_ON_ERROR" = false ]; then
            echo -e "${RED}测试中止${NC}"
            exit 1
        fi
    fi
    echo ""
}

# 测试函数
test_basic_connectivity() {
    local ALL_OK=true
    check_http "$FRONTEND_URL" "200" "前端" || ALL_OK=false
    check_http "$BACKEND_URL/health" "200" "后端健康" || ALL_OK=false
    check_http "$DETECTION_URL/health" "200" "检测服务健康" || ALL_OK=false
    check_http "$PLANNING_URL/health" "200" "规划服务健康" || ALL_OK=false
    $ALL_OK
}

test_api_docs() {
    local ALL_OK=true
    check_http "$BACKEND_URL/docs" "200" "后端 API 文档" || ALL_OK=false
    check_http "$DETECTION_URL/docs" "200" "检测服务 API 文档" || ALL_OK=false
    check_http "$PLANNING_URL/docs" "200" "规划服务 API 文档" || ALL_OK=false
    $ALL_OK
}

test_service_connectivity() {
    local ALL_OK=true
    if docker exec ruralbrain-backend curl -s -f http://detection-service:8001/health > /dev/null 2>&1; then
        [ "$VERBOSE" = true ] && echo -e "  ${GREEN}✓ 后端 → 检测服务${NC}"
    else
        echo -e "  ${RED}✗ 后端 → 检测服务 不连通${NC}"
        ALL_OK=false
    fi
    if docker exec ruralbrain-backend curl -s -f http://planning-service:8003/health > /dev/null 2>&1; then
        [ "$VERBOSE" = true ] && echo -e "  ${GREEN}✓ 后端 → 规划服务${NC}"
    else
        echo -e "  ${RED}✗ 后端 → 规划服务 不连通${NC}"
        ALL_OK=false
    fi
    $ALL_OK
}

test_detection_service() {
    local TEST_TYPE=$1
    local ENDPOINT=$2
    local TEST_IMAGE=$3

    if [ ! -f "$TEST_IMAGE" ]; then
        echo -e "  ${YELLOW}⚠ 测试图片不存在，跳过${NC}"
        return 0
    fi

    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$ENDPOINT" \
        -F "file=@$TEST_IMAGE" \
        --max-time $TIMEOUT 2>/dev/null)

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

    if [ "$HTTP_CODE" = "200" ]; then
        if [ "$VERBOSE" = true ]; then
            BODY=$(echo "$RESPONSE" | sed '$d')
            echo -e "  ${GREEN}✓ 检测成功${NC}"
            echo "$BODY" | head -3
        fi
        return 0
    else
        echo -e "  ${RED}✗ HTTP $HTTP_CODE${NC}"
        return 1
    fi
}

test_pest_detection() {
    test_detection_service "病虫害" "$DETECTION_URL/detection/pest/detect" "$RESOURCES_DIR/pests/1.jpg"
}

test_rice_detection() {
    test_detection_service "大米" "$DETECTION_URL/detection/rice/predict" "$RESOURCES_DIR/rice/1.jpg"
}

test_cow_detection() {
    test_detection_service "奶牛" "$DETECTION_URL/detection/cow/detect" "$RESOURCES_DIR/cows/1.jpg"
}

test_planning_documents() {
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        "$PLANNING_URL/api/v1/knowledge/documents" \
        --max-time $TIMEOUT 2>/dev/null)

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

    if [ "$HTTP_CODE" = "200" ]; then
        if [ "$VERBOSE" = true ]; then
            echo -e "  ${GREEN}✓ 文档列表获取成功${NC}"
        fi
        return 0
    else
        echo -e "  ${RED}✗ HTTP $HTTP_CODE${NC}"
        return 1
    fi
}

test_agent_chat() {
    RESPONSE=$(timeout 60 curl -s -N \
        -X POST "$BACKEND_URL/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "你好，请介绍一下自己"}' \
        2>/dev/null | head -5)

    if echo "$RESPONSE" | grep -q "type.*start"; then
        if [ "$VERBOSE" = true ]; then
            echo -e "  ${GREEN}✓ Agent 响应正常${NC}"
        fi
        return 0
    else
        echo -e "  ${RED}✗ Agent 无响应${NC}"
        return 1
    fi
}

test_frontend_static() {
    if curl -s --head "$FRONTEND_URL/_next/static" --max-time $TIMEOUT | grep -q "HTTP"; then
        [ "$VERBOSE" = true ] && echo -e "  ${GREEN}✓ 静态资源可访问${NC}"
        return 0
    else
        echo -e "  ${YELLOW}⚠ 静态资源可能未构建${NC}"
        return 0
    fi
}

run_test_mode() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  RuralBrain 功能测试${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "测试级别: ${YELLOW}$TEST_LEVEL${NC}"
    echo ""

    # 1. 基础连通性测试（所有级别）
    run_test "基础连通性" "test_basic_connectivity" "fast"
    run_test "API 文档可访问性" "test_api_docs" "fast"
    run_test "服务间网络连通性" "test_service_connectivity" "fast"

    # 2. 检测服务测试（normal 及以上）
    run_test "病虫害检测" "test_pest_detection" "normal"
    run_test "大米识别" "test_rice_detection" "normal"
    run_test "奶牛检测" "test_cow_detection" "normal"

    # 3. 规划和 Agent 测试（full）
    run_test "规划服务文档列表" "test_planning_documents" "full"
    run_test "Agent 通用对话" "test_agent_chat" "full"
    run_test "前端静态资源" "test_frontend_static" "full"

    # 测试摘要
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  测试摘要${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "测试级别: ${YELLOW}$TEST_LEVEL${NC}"
    echo -e "总测试数: ${BLUE}$TESTS_TOTAL${NC}"
    echo -e "通过: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "失败: ${RED}$TESTS_FAILED${NC}"
    echo -e "${BLUE}========================================${NC}"

    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ 所有测试通过！${NC}"
    else
        echo -e "${RED}✗ 部分测试失败${NC}"
    fi

    exit $EXIT_CODE
}

# ===== 主入口 =====

if [ "$MODE" = "health" ]; then
    run_health_check
else
    run_test_mode
fi

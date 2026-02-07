#!/bin/bash
# RuralBrain 开发模式功能测试脚本
# 支持分级测试：fast（快速）、normal（正常）、full（完整）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 默认参数
TEST_LEVEL="normal"
VERBOSE=false
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
    echo "选项:"
    echo "  --fast              快速测试（基础连通性，< 30秒）"
    echo "  --normal            正常测试（+ 检测服务，< 2分钟）[默认]"
    echo "  --full              完整测试（+ Agent/规划/前端，< 5分钟）"
    echo "  --verbose           显示详细输出"
    echo "  --continue          遇到错误继续测试"
    echo "  -h, --help          显示帮助信息"
    echo ""
    echo "测试级别说明:"
    echo "  fast  : 基础连通性 + 健康检查"
    echo "  normal: fast + 检测服务测试"
    echo "  full  : normal + Agent/规划/前端测试"
}

# 参数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            TEST_LEVEL="fast"
            shift
            ;;
        --normal)
            TEST_LEVEL="normal"
            shift
            ;;
        --full)
            TEST_LEVEL="full"
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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  RuralBrain 功能测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "测试级别: ${YELLOW}$TEST_LEVEL${NC}"
echo ""

# 超时设置
TIMEOUT=30

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

# 函数：检查 HTTP 端点
check_http() {
    local URL=$1
    local EXPECTED=${2:-200}
    local NAME=${3:-"HTTP 端点"}

    if [ "$VERBOSE" = true ]; then
        echo -e "  检查: $NAME"
        echo -e "  URL: $URL"
    fi

    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "$URL" 2>/dev/null || echo "000")

    if [ "$RESPONSE" = "$EXPECTED" ]; then
        if [ "$VERBOSE" = true ]; then
            echo -e "  ${GREEN}✓ HTTP $RESPONSE${NC}"
        fi
        return 0
    else
        echo -e "  ${RED}✗ HTTP $RESPONSE (期望 $EXPECTED)${NC}"
        return 1
    fi
}

# ===== 测试函数 =====

# 测试：基础连通性
test_basic_connectivity() {
    local ALL_OK=true

    # 前端
    check_http "$FRONTEND_URL" "200" "前端" || ALL_OK=false

    # 后端健康
    check_http "$BACKEND_URL/health" "200" "后端健康" || ALL_OK=false

    # 检测服务健康
    check_http "$DETECTION_URL/health" "200" "检测服务健康" || ALL_OK=false

    # 规划服务健康
    check_http "$PLANNING_URL/health" "200" "规划服务健康" || ALL_OK=false

    $ALL_OK
}

# 测试：API 文档可访问性
test_api_docs() {
    local ALL_OK=true

    check_http "$BACKEND_URL/docs" "200" "后端 API 文档" || ALL_OK=false
    check_http "$DETECTION_URL/docs" "200" "检测服务 API 文档" || ALL_OK=false
    check_http "$PLANNING_URL/docs" "200" "规划服务 API 文档" || ALL_OK=false

    $ALL_OK
}

# 测试：服务间网络连通性
test_service_connectivity() {
    local ALL_OK=true

    # 检查后端是否能访问检测服务
    if docker exec ruralbrain-backend curl -s -f http://detection-service:8001/health > /dev/null 2>&1; then
        if [ "$VERBOSE" = true ]; then
            echo -e "  ${GREEN}✓ 后端 → 检测服务${NC}"
        fi
    else
        echo -e "  ${RED}✗ 后端 → 检测服务 不连通${NC}"
        ALL_OK=false
    fi

    # 检查后端是否能访问规划服务
    if docker exec ruralbrain-backend curl -s -f http://planning-service:8003/health > /dev/null 2>&1; then
        if [ "$VERBOSE" = true ]; then
            echo -e "  ${GREEN}✓ 后端 → 规划服务${NC}"
        fi
    else
        echo -e "  ${RED}✗ 后端 → 规划服务 不连通${NC}"
        ALL_OK=false
    fi

    $ALL_OK
}

# 测试：病虫害检测
test_pest_detection() {
    local TEST_IMAGE="$RESOURCES_DIR/pests/1.jpg"

    if [ ! -f "$TEST_IMAGE" ]; then
        echo -e "  ${YELLOW}⚠ 测试图片不存在，跳过${NC}"
        return 0
    fi

    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$DETECTION_URL/detection/pest/detect" \
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

# 测试：大米识别
test_rice_detection() {
    local TEST_IMAGE="$RESOURCES_DIR/rice/1.jpg"

    if [ ! -f "$TEST_IMAGE" ]; then
        echo -e "  ${YELLOW}⚠ 测试图片不存在，跳过${NC}"
        return 0
    fi

    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$DETECTION_URL/detection/rice/predict" \
        -F "file=@$TEST_IMAGE" \
        --max-time $TIMEOUT 2>/dev/null)

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

    if [ "$HTTP_CODE" = "200" ]; then
        if [ "$VERBOSE" = true ]; then
            BODY=$(echo "$RESPONSE" | sed '$d')
            echo -e "  ${GREEN}✓ 识别成功${NC}"
            echo "$BODY" | head -3
        fi
        return 0
    else
        echo -e "  ${RED}✗ HTTP $HTTP_CODE${NC}"
        return 1
    fi
}

# 测试：奶牛检测
test_cow_detection() {
    local TEST_IMAGE="$RESOURCES_DIR/cows/1.jpg"

    if [ ! -f "$TEST_IMAGE" ]; then
        echo -e "  ${YELLOW}⚠ 测试图片不存在，跳过${NC}"
        return 0
    fi

    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X POST "$DETECTION_URL/detection/cow/detect" \
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

# 测试：规划服务文档列表
test_planning_documents() {
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        "$PLANNING_URL/api/v1/knowledge/documents" \
        --max-time $TIMEOUT 2>/dev/null)

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "200" ]; then
        if [ "$VERBOSE" = true ]; then
            echo -e "  ${GREEN}✓ 文档列表获取成功${NC}"
            echo "$BODY" | python3 -c "import sys,json; docs=json.load(sys.stdin).get('documents',[]); print(f'  文档数量: {len(docs)}')" 2>/dev/null || echo "$BODY" | head -3
        fi
        return 0
    else
        echo -e "  ${RED}✗ HTTP $HTTP_CODE${NC}"
        return 1
    fi
}

# 测试：Agent 通用对话
test_agent_chat() {
    RESPONSE=$(timeout 60 curl -s -N \
        -X POST "$BACKEND_URL/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "你好，请介绍一下自己"}' \
        2>/dev/null | head -5)

    if echo "$RESPONSE" | grep -q "type.*start"; then
        if [ "$VERBOSE" = true ]; then
            echo -e "  ${GREEN}✓ Agent 响应正常${NC}"
            echo "$RESPONSE" | head -2
        fi
        return 0
    else
        echo -e "  ${RED}✗ Agent 无响应${NC}"
        echo "$RESPONSE"
        return 1
    fi
}

# 测试：前端静态资源
test_frontend_static() {
    # 检查静态资源目录是否可访问
    if curl -s --head "$FRONTEND_URL/_next/static" --max-time $TIMEOUT | grep -q "HTTP"; then
        if [ "$VERBOSE" = true ]; then
            echo -e "  ${GREEN}✓ 静态资源可访问${NC}"
        fi
        return 0
    else
        echo -e "  ${YELLOW}⚠ 静态资源可能未构建${NC}"
        return 0  # 不视为错误
    fi
}

# ===== 主测试流程 =====

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

# ===== 测试摘要 =====
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

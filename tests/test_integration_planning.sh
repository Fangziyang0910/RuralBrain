#!/bin/bash
# Backend → Planning Service 集成测试脚本

set -e

BACKEND_URL="http://localhost:8080"
PLANNING_URL="http://localhost:8003"

echo "🧪 Backend → Planning Service 集成测试"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 测试函数
test_endpoint() {
    local name=$1
    local url=$2
    local method=$3
    local data=$4

    echo -n "测试 $name... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$url" 2>/dev/null)
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ] || [ "$http_code" = "204" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $http_code)"
        echo "响应: $body"
        return 1
    fi
}

# 检查服务是否运行
check_service() {
    local name=$1
    local url=$2

    echo -n "检查 $name... "
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}运行中${NC}"
        return 0
    else
        echo -e "${RED}未运行${NC}"
        return 1
    fi
}

# 1. 检查服务状态
echo "1. 服务状态检查"
check_service "Planning Service" "$PLANNING_URL/health"
check_service "Backend" "$BACKEND_URL/health"
echo ""

# 2. 测试 Planning Service 直接访问
echo "2. Planning Service 直接访问测试"
test_endpoint "健康检查" "$PLANNING_URL/health" "GET"
test_endpoint "文档列表" "$PLANNING_URL/api/v1/knowledge/documents" "GET"
echo ""

# 3. 测试 Backend 代理功能
echo "3. Backend → Planning Service 代理测试"

# 简单问题
echo -e "${YELLOW}测试: 简单问候${NC}"
response=$(timeout 30 curl -s -N \
    -X POST "$BACKEND_URL/chat/planning" \
    -H "Content-Type: application/json" \
    -d '{"message": "你好"}' 2>/dev/null | head -5)

if echo "$response" | grep -q "type.*start"; then
    echo -e "${GREEN}✅ 简单问候测试通过${NC}"
else
    echo -e "${RED}❌ 简单问候测试失败${NC}"
    echo "响应: $response"
fi
echo ""

# 规划问题
echo -e "${YELLOW}测试: 规划咨询${NC}"
response=$(timeout 60 curl -s -N \
    -X POST "$BACKEND_URL/chat/planning" \
    -H "Content-Type: application/json" \
    -d '{"message": "知识库里有哪些文档？"}' 2>/dev/null | head -10)

if echo "$response" | grep -q "tool.*list_available_documents"; then
    echo -e "${GREEN}✅ 规划咨询测试通过（工具调用正常）${NC}"
else
    echo -e "${RED}❌ 规划咨询测试失败${NC}"
    echo "响应: $response"
fi
echo ""

# 4. 测试错误处理
echo "4. 错误处理测试"

echo -n "测试无效端点... "
response=$(curl -s -w "\n%{http_code}" \
    "$BACKEND_URL/chat/invalid" 2>/dev/null)
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" = "404" ] || [ "$http_code" = "405" ]; then
    echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code)"
else
    echo -e "${RED}❌ FAIL${NC} (HTTP $http_code)"
fi
echo ""

# 5. 端到端测试
echo "5. 端到端测试"
echo -e "${YELLOW}场景: 用户询问长宁镇旅游发展${NC}"

echo "发送请求到 Backend..."
timeout 90 curl -s -N \
    -X POST "$BACKEND_URL/chat/planning" \
    -H "Content-Type: application/json" \
    -d '{"message": "长宁镇的旅游发展目标是什么？", "mode": "fast"}' \
    2>/dev/null | head -20 | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
        event_type=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('type',''))" 2>/dev/null || echo "")
        case $event_type in
            "start")
                echo -e "  ${GREEN}▶️  会话开始${NC}"
                ;;
            "content")
                content=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('content','')[:20] + '...' if len(json.load(sys.stdin).get('content','')) > 20 else json.load(sys.stdin).get('content',''))" 2>/dev/null || echo "")
                echo -e "  ${BLUE}📝 $content${NC}"
                ;;
            "tool")
                tool=$(echo "$line" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")
                echo -e "  ${YELLOW}🔧 工具: $tool${NC}"
                ;;
            "end")
                echo -e "  ${GREEN}✅ 会话结束${NC}"
                ;;
        fi
    fi
done

echo ""
echo "======================================"
echo -e "${GREEN}✅ 集成测试完成！${NC}"
echo ""
echo "💡 提示："
echo "  - Backend API: $BACKEND_URL/docs"
echo "  - Planning API: $PLANNING_URL/docs"
echo "  - 查看日志: docker-compose logs -f"

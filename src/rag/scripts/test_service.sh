#!/bin/bash
# Planning Service API 测试脚本

set -e

BASE_URL="http://localhost:8003"

echo "🧪 Planning Service API 测试"
echo "============================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3

    echo -n "测试 $name... "

    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected" ]; then
        echo -e "${GREEN}✅ PASS${NC} (HTTP $http_code)"
        if [ -n "$body" ] && [ "$body" != "null" ]; then
            echo "$body" | python3 -m json.tool 2>/dev/null | head -20 || echo "$body" | head -5
        fi
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $http_code, expected $expected)"
        echo "$body"
        return 1
    fi
    echo ""
}

# 1. 健康检查
test_endpoint "健康检查" "$BASE_URL/health" "200"

# 2. 根路径
test_endpoint "根路径" "$BASE_URL/" "200"

# 3. 文档列表
test_endpoint "文档列表" "$BASE_URL/api/v1/knowledge/documents" "200"

# 4. 文档摘要（URL 编码）
SOURCE=$(curl -s "$BASE_URL/api/v1/knowledge/documents" | python3 -c "import sys,json; print(json.load(sys.stdin)['documents'][0]['source'])" 2>/dev/null || echo "")
if [ -n "$SOURCE" ]; then
    echo "测试文档摘要: $SOURCE"
    ENCODED_SOURCE=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$SOURCE'))")
    test_endpoint "文档摘要" "$BASE_URL/api/v1/knowledge/summary/$ENCODED_SOURCE" "200"
fi

echo "============================"
echo -e "${GREEN}✅ 所有测试完成！${NC}"
echo ""
echo "📚 API 文档: $BASE_URL/docs"
echo "📊 ReDoc 文档: $BASE_URL/redoc"

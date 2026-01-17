#!/bin/bash
# Planning Service 流式聊天测试脚本

set -e

BASE_URL="http://localhost:8003"

echo "💬 Planning Service 流式聊天测试"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 测试问题列表
QUESTIONS=(
    "长宁镇的旅游发展目标是什么？"
    "博罗古城有什么特色？"
    "罗浮山周边有哪些产业发展？"
)

# 测试函数
test_stream_chat() {
    local question=$1
    local mode=$2
    local thread_id=$3

    echo -e "${BLUE}📝 问题: ${question}${NC}"
    echo -e "${YELLOW}🔧 模式: ${mode}${NC}"
    echo ""

    # 构建请求数据
    request_data=$(cat <<EOF
{
  "message": "${question}",
  "mode": "${mode}",
  "thread_id": "${thread_id}"
}
EOF
)

    # 发送请求并解析 SSE 流
    echo -e "${GREEN}🤖 AI 响应:${NC}"
    echo "--------------------------------"

    response=$(curl -s -N \
        -H "Content-Type: application/json" \
        -d "$request_data" \
        "$BASE_URL/api/v1/chat/planning" 2>/dev/null)

    if [ -z "$response" ]; then
        echo -e "${RED}❌ 无响应${NC}"
        return 1
    fi

    # 解析 SSE 事件
    tools_used=()
    content_blocks=0
    has_error=false

    while IFS= read -r line; do
        if [[ $line == data:* ]]; then
            json_data="${line#data: }"

            # 解析 JSON
            event_type=$(echo "$json_data" | python3 -c "import sys,json; print(json.load(sys.stdin).get('type',''))" 2>/dev/null || echo "")

            case $event_type in
                "start")
                    echo -e "${BLUE}▶️  会话开始${NC}"
                    ;;
                "content")
                    content=$(echo "$json_data" | python3 -c "import sys,json; print(json.load(sys.stdin).get('content',''), end='')" 2>/dev/null || echo "")
                    echo -n "$content"
                    content_blocks=$((content_blocks + 1))
                    ;;
                "tool")
                    tool_name=$(echo "$json_data" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")
                    status=$(echo "$json_data" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")
                    if [ "$status" = "started" ]; then
                        echo ""
                        echo -e "${YELLOW}🔧 调用工具: $tool_name${NC}"
                    fi
                    # 记录使用的工具
                    if [[ ! " ${tools_used[@]} " =~ " ${tool_name} " ]]; then
                        tools_used+=("$tool_name")
                    fi
                    ;;
                "end")
                    echo ""
                    echo -e "${GREEN}✅ 会话结束${NC}"
                    ;;
                "error")
                    error_msg=$(echo "$json_data" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error',''))" 2>/dev/null || echo "")
                    echo -e "${RED}❌ 错误: $error_msg${NC}"
                    has_error=true
                    ;;
            esac
        fi
    done <<< "$response"

    echo "--------------------------------"
    echo -e "${GREEN}📊 统计:${NC}"
    echo "  - 内容块数: $content_blocks"
    echo "  - 使用工具: ${tools_used[*]:-无}"

    if [ "$has_error" = true ]; then
        echo -e "${RED}  - 状态: ❌ 失败${NC}"
        return 1
    else
        echo -e "${GREEN}  - 状态: ✅ 成功${NC}"
    fi

    echo ""
}

# 生成唯一线程 ID
THREAD_ID="test-$(date +%s)"

echo "测试会话 ID: $THREAD_ID"
echo ""

# 运行测试
for question in "${QUESTIONS[@]}"; do
    test_stream_chat "$question" "auto" "$THREAD_ID"
    echo ""
    sleep 1
done

echo "=================================="
echo -e "${GREEN}✅ 流式聊天测试完成！${NC}"
echo ""
echo "💡 提示："
echo "  - 查看完整 API 文档: $BASE_URL/docs"
echo "  - 查看服务日志以了解 Agent 思考过程"

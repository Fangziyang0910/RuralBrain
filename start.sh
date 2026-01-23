#!/bin/bash
# RuralBrain 一键启动脚本

set -e

echo "🚀 RuralBrain 一键启动"
echo "======================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查环境变量
echo "1. 检查环境配置..."
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ 错误: .env 文件不存在${NC}"
    echo "请先复制 .env.example 为 .env 并配置 API 密钥"
    echo ""
    echo "  cp .env.example .env"
    echo "  nano .env  # 编辑配置"
    exit 1
fi

# 检查 API 密钥
if ! grep -q "DEEPSEEK_API_KEY=sk-" .env && ! grep -q "ZHIPUAI_API_KEY=" .env; then
    echo -e "${YELLOW}⚠️  警告: 未检测到有效的 API 密钥${NC}"
    echo "请在 .env 文件中配置 DEEPSEEK_API_KEY 或 ZHIPUAI_API_KEY"
    echo ""
    read -p "是否继续启动？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo -e "${GREEN}✅ 环境配置检查通过${NC}"
echo ""

# 检查知识库
echo "2. 检查知识库..."
if [ ! -d "knowledge_base/chroma_db" ]; then
    echo -e "${YELLOW}⚠️  知识库不存在，准备构建...${NC}"
    echo ""
    if [ -f "src/rag/scripts/build_kb_auto.py" ]; then
        python3 src/rag/scripts/build_kb_auto.py
    elif [ -f "src/rag/build.py" ]; then
        python3 src/rag/build.py
    else
        echo -e "${RED}❌ 错误: 找不到知识库构建脚本${NC}"
        exit 1
    fi
    echo ""
fi
echo -e "${GREEN}✅ 知识库检查通过${NC}"
echo ""

# 选择启动模式
echo "3. 选择启动模式"
echo "  1) Planning Service（规划咨询）"
echo "  2) Backend（主 API 网关）"
echo "  3) 全部服务"
echo "  4) Docker 模式"
echo ""
read -p "请选择 (1-4): " choice
echo ""

case $choice in
    1)
        echo "启动 Planning Service..."
        chmod +x src/rag/scripts/start_with_env.sh
        src/rag/scripts/start_with_env.sh
        ;;
    2)
        echo "启动 Backend..."
        chmod +x start_backend.sh
        ./start_backend.sh
        ;;
    3)
        echo "启动 Planning Service..."
        chmod +x src/rag/scripts/start_with_env.sh
        src/rag/scripts/start_with_env.sh &
        PLANNING_PID=$!

        sleep 3

        echo "启动 Backend..."
        chmod +x start_backend.sh
        ./start_backend.sh &
        BACKEND_PID=$!

        echo ""
        echo -e "${GREEN}✅ 全部服务已启动${NC}"
        echo ""
        echo "服务信息:"
        echo "  - Planning Service: http://localhost:8003"
        echo "  - Backend: http://localhost:8080"
        echo ""
        echo "PID: $PLANNING_PID, $BACKEND_PID"
        echo ""
        echo "按 Ctrl+C 停止所有服务"

        # 等待进程
        wait $PLANNING_PID $BACKEND_PID
        ;;
    4)
        echo "Docker 模式启动..."
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}❌ 错误: Docker 未安装${NC}"
            exit 1
        fi

        docker-compose up -d

        echo ""
        echo -e "${GREEN}✅ Docker 服务已启动${NC}"
        echo ""
        echo "服务信息:"
        echo "  - Frontend: http://localhost:3000"
        echo "  - Backend: http://localhost:8080"
        echo "  - Planning Service: http://localhost:8003"
        echo ""
        echo "查看日志: docker-compose logs -f"
        echo "停止服务: docker-compose down"
        ;;
    *)
        echo -e "${RED}❌ 无效选择${NC}"
        exit 1
        ;;
esac

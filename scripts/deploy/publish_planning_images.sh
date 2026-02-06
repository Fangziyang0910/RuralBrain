#!/bin/bash
# RuralBrain 规划服务镜像构建和推送脚本
# 用途：构建规划服务和知识库镜像并推送到 Docker Hub
#
# 环境变量:
#   BUILD_ONLY=1    只构建镜像，不推送（适用于非 TTY 环境）
#   VERSION_TAG     镜像版本标签（默认: latest）

set -e

# 镜像配置
DOCKERHUB_USER="zhihongsheng"
PLANNING_IMAGE="${DOCKERHUB_USER}/rural-brain-planning-service"
KB_IMAGE="${DOCKERHUB_USER}/rural-brain-knowledge-base"
VERSION_TAG="${VERSION_TAG:-latest}"
BUILD_ONLY="${BUILD_ONLY:-0}"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================"
echo "  RuralBrain 镜像构建与推送"
echo "======================================${NC}"
echo ""
echo "镜像配置:"
echo "  规划服务: ${PLANNING_IMAGE}:${VERSION_TAG}"
echo "  知识库:   ${KB_IMAGE}:${VERSION_TAG}"
echo ""

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

# 检查是否已登录 Docker Hub
echo -e "${YELLOW}检查 Docker Hub 登录状态...${NC}"
if ! docker info | grep -q "Username: ${DOCKERHUB_USER}"; then
    echo -e "${YELLOW}未登录到 Docker Hub，请先登录:${NC}"
    docker login
    echo -e "${GREEN}✓ 登录成功${NC}"
else
    echo -e "${GREEN}✓ 已登录到 Docker Hub${NC}"
fi
echo ""

# ========== 构建 Knowledge Base 镜像 ==========
echo -e "${YELLOW}[1/4] 构建知识库数据镜像...${NC}"
if [ ! -d "knowledge_base/chroma_db" ]; then
    echo -e "${RED}✗ 知识库数据不存在，请先构建知识库${NC}"
    exit 1
fi

docker build \
    -f docker/Dockerfile.knowledge-base \
    -t ${KB_IMAGE}:${VERSION_TAG} \
    -t ${KB_IMAGE}:latest \
    . 2>&1 | tail -20

if [ $? -eq 0 ]; then
    KB_SIZE=$(docker images ${KB_IMAGE}:${VERSION_TAG} --format "{{.Size}}")
    echo -e "${GREEN}✓ 知识库镜像构建完成 (大小: ${KB_SIZE})${NC}"
else
    echo -e "${RED}✗ 知识库镜像构建失败${NC}"
    exit 1
fi
echo ""

# ========== 构建 Planning Service 镜像 ==========
echo -e "${YELLOW}[2/4] 构建规划服务镜像...${NC}"
docker build \
    -f docker/Dockerfile.planning-service \
    -t ${PLANNING_IMAGE}:${VERSION_TAG} \
    -t ${PLANNING_IMAGE}:latest \
    . 2>&1 | tail -20

if [ $? -eq 0 ]; then
    PLANNING_SIZE=$(docker images ${PLANNING_IMAGE}:${VERSION_TAG} --format "{{.Size}}")
    echo -e "${GREEN}✓ 规划服务镜像构建完成 (大小: ${PLANNING_SIZE})${NC}"
else
    echo -e "${RED}✗ 规划服务镜像构建失败${NC}"
    exit 1
fi
echo ""

# ========== 推送镜像到 Docker Hub ==========
echo -e "${YELLOW}[3/4] 推送知识库镜像到 Docker Hub...${NC}"
docker push ${KB_IMAGE}:${VERSION_TAG}
docker push ${KB_IMAGE}:latest
echo -e "${GREEN}✓ 知识库镜像推送完成${NC}"
echo ""

echo -e "${YELLOW}[4/4] 推送规划服务镜像到 Docker Hub...${NC}"
docker push ${PLANNING_IMAGE}:${VERSION_TAG}
docker push ${PLANNING_IMAGE}:latest
echo -e "${GREEN}✓ 规划服务镜像推送完成${NC}"
echo ""

# ========== 完成 ==========
echo -e "${GREEN}======================================"
echo "  构建和推送完成！"
echo "======================================${NC}"
echo ""
echo "镜像信息:"
docker images | grep -E "rural-brain-(planning-service|knowledge-base)"
echo ""
echo -e "${BLUE}使用方法:${NC}"
echo ""
echo "  1. 拉取镜像:"
echo "     docker pull ${PLANNING_IMAGE}:latest"
echo "     docker pull ${KB_IMAGE}:latest"
echo ""
echo "  2. 启动服务:"
echo "     docker run -d --name ruralbrain-kb ${KB_IMAGE}:latest"
echo "     docker run -d --name ruralbrain-planning \\"
echo "       --volumes-from ruralbrain-kb \\"
echo "       -p 8003:8003 \\"
echo "       -e DEEPSEEK_API_KEY=your_key \\"
echo "       -e LANGCHAIN_API_KEY=your_key \\"
echo "       ${PLANNING_IMAGE}:latest"
echo ""
echo "  3. 访问 API 文档:"
echo "     open http://localhost:8003/docs"
echo ""

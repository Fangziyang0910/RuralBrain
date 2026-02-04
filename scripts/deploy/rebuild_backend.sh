#!/bin/bash
# RuralBrain 后端镜像重新构建和推送脚本
# 在开发机（有源代码的机器）上运行

set -e

echo "======================================"
echo "  重新构建并推送后端镜像"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 构建后端镜像
echo -e "${YELLOW}[1/3] 构建后端镜像...${NC}"
docker build -f docker/Dockerfile.backend -t zhihongsheng/rural-brain-backend:latest .
echo -e "${GREEN}✓ 后端镜像构建完成${NC}"
echo ""

# 2. 推送镜像
echo -e "${YELLOW}[2/3] 推送镜像到 Docker Hub...${NC}"
docker push zhihongsheng/rural-brain-backend:latest
echo -e "${GREEN}✓ 镜像推送完成${NC}"
echo ""

# 3. 更新部署服务器（远程）
echo -e "${YELLOW}[3/3] 提示：请在部署服务器上执行更新命令${NC}"
echo ""
echo "  cd ~/ruralbrain-deploy"
echo "  docker pull zhihongsheng/rural-brain-backend:latest"
echo "  docker-compose up -d --force-recreate backend"
echo ""
echo -e "${GREEN}======================================"
echo "  构建完成！"
echo "======================================${NC}"

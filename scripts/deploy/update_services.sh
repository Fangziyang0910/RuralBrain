#!/bin/bash
# RuralBrain 服务更新脚本
# 在部署服务器上执行此脚本
# 使用方法: cd ~/ruralbrain-deploy && bash /path/to/update_services.sh

set -e  # 遇到错误立即退出

echo "======================================"
echo "  RuralBrain 服务更新"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 拉取最新代码
echo -e "${YELLOW}[1/4] 拉取最新代码...${NC}"
git pull origin main
echo -e "${GREEN}✓ 代码更新完成${NC}"
echo ""

# 2. 拉取最新镜像
echo -e "${YELLOW}[2/4] 拉取最新镜像...${NC}"
docker pull zhihongsheng/rural-brain-backend:latest
docker pull zhihongsheng/rural-brain-planning-service:latest
echo -e "${GREEN}✓ 镜像拉取完成${NC}"
echo ""

# 3. 停止并删除旧容器（保留数据卷）
echo -e "${YELLOW}[3/4] 更新服务...${NC}"
docker-compose -f docker-compose.deploy.yml up -d backend planning-service
echo -e "${GREEN}✓ 服务更新完成${NC}"
echo ""

# 4. 查看服务状态
echo -e "${YELLOW}[4/4] 服务状态...${NC}"
docker-compose -f docker-compose.deploy.yml ps
echo ""

echo -e "${GREEN}======================================"
echo "  更新完成！"
echo "======================================${NC}"
echo ""
echo "查看实时日志:"
echo "  docker-compose -f docker-compose.deploy.yml logs -f backend"
echo ""
echo "单独查看服务状态:"
echo "  docker-compose -f docker-compose.deploy.yml ps"

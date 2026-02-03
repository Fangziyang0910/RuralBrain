#!/bin/bash
# ====================================
# RuralBrain 一键部署脚本（自包含版本）
# ====================================

set -e

echo "=================================="
echo "  RuralBrain 一键部署"
echo "=================================="

GREEN='\033[0;32m'
NC='\033[0m'

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "Docker 未安装，请先安装 Docker"
    exit 1
fi

# 拉取镜像
echo "正在拉取镜像..."
docker pull zhihongsheng/rural-brain-portal:latest
docker pull zhihongsheng/rural-brain-frontend:latest
docker pull zhihongsheng/rural-brain-backend:latest
docker pull zhihongsheng/rural-brain-pest-detector:latest
docker pull zhihongsheng/rural-brain-planning-service:latest

# 创建目录
mkdir -p ~/ruralbrain-deploy
cd ~/ruralbrain-deploy

# 直接写入 docker-compose.yml
cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'
services:
  portal:
    image: zhihongsheng/rural-brain-portal:latest
    container_name: rural-brain-portal
    ports:
      - "3000:80"
    restart: always
  frontend:
    image: zhihongsheng/rural-brain-frontend:latest
    container_name: rural-brain-frontend
    ports:
      - "3001:3000"
    environment:
      - NODE_ENV=production
      - BACKEND_URL=http://backend:8081
    depends_on:
      - backend
    restart: always
  backend:
    image: zhihongsheng/rural-brain-backend:latest
    container_name: rural-brain-backend
    ports:
      - "8081:8081"
    environment:
      - ENVIRONMENT=production
      - PLANNING_SERVICE_URL=http://planning-service:8003
      - PEST_DETECTION_API_URL=http://detection-gateway:8001/detection/pest/detect
      - RICE_DETECTION_API_URL=http://detection-gateway:8001/detection/rice/predict
      - COW_DETECTION_API_URL=http://detection-gateway:8001/detection/cow/detect
    depends_on:
      - detection-gateway
      - planning-service
    restart: always
  detection-gateway:
    image: zhihongsheng/rural-brain-pest-detector:latest
    container_name: rural-brain-detection-gateway
    ports:
      - "8001:8001"
    restart: always
  planning-service:
    image: zhihongsheng/rural-brain-planning-service:latest
    container_name: rural-brain-planning-service
    ports:
      - "8003:8003"
    restart: always
COMPOSE_EOF

# 启动服务
echo "启动服务..."
docker-compose up -d

sleep 5

echo ""
echo -e "${GREEN}部署完成！${NC}"
echo ""
echo "访问地址："
echo "  - 门户页面: http://localhost:3000"
echo "  - 乡村智慧大脑: http://localhost:3001"
echo ""
echo "常用命令："
echo "  cd ~/ruralbrain-deploy && docker-compose ps"
echo "  cd ~/ruralbrain-deploy && docker-compose logs"

#!/bin/bash
# ====================================
# RuralBrain 一键部署脚本
# 适用于新电脑快速部署
# ====================================

set -e  # 遇到错误立即退出

echo "=================================="
echo "  RuralBrain 一键部署脚本"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否为 root 用户
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}请勿使用 root 用户运行此脚本${NC}"
    exit 1
fi

# 检测操作系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo -e "${GREEN}检测到 Linux 系统${NC}"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo -e "${GREEN}检测到 macOS 系统${NC}"
else
    echo -e "${RED}不支持的操作系统: $OSTYPE${NC}"
    exit 1
fi

# 1. 安装 Docker
echo ""
echo "=================================="
echo "步骤 1/5: 检查/安装 Docker"
echo "=================================="

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker 未安装，开始安装...${NC}"

    if [ "$OS" == "linux" ]; then
        # Linux 安装 Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh

        # 将当前用户添加到 docker 组
        sudo usermod -aG docker $USER

        echo -e "${YELLOW}请注销后重新登录，或运行以下命令使组权限生效：${NC}"
        echo "  newgrp docker"

        rm get-docker.sh
    elif [ "$OS" == "macos" ]; then
        echo -e "${YELLOW}请手动安装 Docker Desktop for Mac${NC}"
        echo "  下载地址: https://www.docker.com/products/docker-desktop/"
        exit 1
    fi
else
    echo -e "${GREEN}Docker 已安装${NC}"
fi

# 2. 安装 Docker Compose
echo ""
echo "=================================="
echo "步骤 2/5: 检查/安装 Docker Compose"
echo "=================================="

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Docker Compose 未安装，开始安装...${NC}"

    if [ "$OS" == "linux" ]; then
        # Linux 安装 Docker Compose
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
else
    echo -e "${GREEN}Docker Compose 已安装${NC}"
fi

# 3. 登录 Docker Hub
echo ""
echo "=================================="
echo "步骤 3/5: 登录 Docker Hub"
echo "=================================="

echo -e "${YELLOW}请输入 Docker Hub 用户名和密码${NC}"
docker login

# 4. 拉取镜像
echo ""
echo "=================================="
echo "步骤 4/5: 拉取 Docker 镜像"
echo "=================================="

echo "正在拉取镜像（这可能需要几分钟）..."
docker pull zhihongsheng/rural-brain-portal:latest
docker pull zhihongsheng/rural-brain-frontend:latest
docker pull zhihongsheng/rural-brain-backend:latest
docker pull zhihongsheng/rural-brain-pest-detector:latest
docker pull zhihongsheng/rural-brain-planning-service:latest

echo -e "${GREEN}镜像拉取完成！${NC}"

# 5. 启动服务
echo ""
echo "=================================="
echo "步骤 5/5: 启动服务"
echo "=================================="

# 创建工作目录
mkdir -p ~/ruralbrain-deploy
cd ~/ruralbrain-deploy

# 下载 docker-compose.yml
echo "下载 docker-compose.yml..."
curl -fsSL https://raw.githubusercontent.com/zhihongsheng/RuralBrain/main/docker/docker-compose.deploy.yml -o docker-compose.yml

# 启动服务
echo "启动所有服务..."
docker-compose up -d

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "=================================="
echo "服务状态"
echo "=================================="
docker-compose ps

# 完成
echo ""
echo "=================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=================================="
echo ""
echo -e "${GREEN}访问地址：${NC}"
echo "  - 门户页面（总入口）: http://localhost:3000"
echo "  - 乡村智慧大脑     : http://localhost:3001"
echo ""
echo -e "${YELLOW}常用命令：${NC}"
echo "  - 查看服务状态: cd ~/ruralbrain-deploy && docker-compose ps"
echo "  - 查看服务日志: cd ~/ruralbrain-deploy && docker-compose logs"
echo "  - 停止所有服务: cd ~/ruralbrain-deploy && docker-compose down"
echo "  - 重启所有服务: cd ~/ruralbrain-deploy && docker-compose restart"
echo ""

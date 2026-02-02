#!/bin/bash
# RuralBrain 离线部署脚本
# 用于在网络受限环境中部署应用

set -e

echo "======================================"
echo "  RuralBrain 离线部署助手"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 步骤 1: 准备前端静态文件
prepare_frontend() {
    echo -e "${YELLOW}[步骤 1/5] 准备前端静态文件...${NC}"

    if [ -f "static.zip" ]; then
        echo "找到 static.zip，正在解压..."
        rm -rf frontend-static
        mkdir -p frontend-static
        unzip -q static.zip -d frontend-static
        echo -e "${GREEN}✓ 前端静态文件准备完成${NC}"
    elif [ -d "frontend-static" ]; then
        echo -e "${GREEN}✓ 前端静态文件目录已存在${NC}"
    else
        echo -e "${RED}✗ 未找到 static.zip 或 frontend-static 目录${NC}"
        echo "请将师兄发来的 static.zip 放在项目根目录"
        exit 1
    fi
    echo ""
}

# 步骤 2: 检查镜像
check_images() {
    echo -e "${YELLOW}[步骤 2/5] 检查 Docker 镜像...${NC}"

    REQUIRED_IMAGES=(
        "ruralbrain-backend:latest"
        "ruralbrain-pest-detector:latest"
        "ruralbrain-rice-detector:latest"
        "ruralbrain-cow-detector:latest"
        "ruralbrain-planning-service:latest"
        "ruralbrain-frontend:deploy"
    )

    MISSING_IMAGES=()

    for image in "${REQUIRED_IMAGES[@]}"; do
        if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${image}$"; then
            echo -e "${GREEN}✓${NC} $image"
        else
            echo -e "${RED}✗${NC} $image (缺失)"
            MISSING_IMAGES+=("$image")
        fi
    done

    if [ ${#MISSING_IMAGES[@]} -gt 0 ]; then
        echo ""
        echo -e "${RED}缺少以下镜像，请先导入：${NC}"
        for img in "${MISSING_IMAGES[@]}"; do
            echo "  - $img"
        done
        echo ""
        echo "导入命令示例："
        echo "  docker load -i ruralbrain-images.tar"
        echo ""
        read -p "是否现在导入？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            load_images
        else
            exit 1
        fi
    else
        echo -e "${GREEN}✓ 所有镜像已就绪${NC}"
    fi
    echo ""
}

# 加载镜像
load_images() {
    echo -e "${YELLOW}正在加载镜像...${NC}"

    if [ -f "ruralbrain-images.tar" ]; then
        docker load -i ruralbrain-images.tar
        echo -e "${GREEN}✓ 镜像加载完成${NC}"
    elif [ -f "ruralbrain-images.tar.gz" ]; then
        gunzip -c ruralbrain-images.tar.gz | docker load
        echo -e "${GREEN}✓ 镜像加载完成${NC}"
    else
        echo -e "${RED}✗ 未找到镜像文件 (ruralbrain-images.tar 或 ruralbrain-images.tar.gz)${NC}"
        exit 1
    fi
    echo ""
}

# 步骤 3: 检查知识库
check_knowledge_base() {
    echo -e "${YELLOW}[步骤 3/5] 检查知识库...${NC}"

    if [ -d "knowledge_base/chroma_db" ]; then
        echo -e "${GREEN}✓ 知识库已存在${NC}"
    else
        echo -e "${YELLOW}⚠ 知识库不存在，某些功能可能无法使用${NC}"
        echo "建议在开发机上运行: uv run python scripts/dev/build_kb_auto.py"
    fi
    echo ""
}

# 步骤 4: 检查环境变量
check_env() {
    echo -e "${YELLOW}[步骤 4/5] 检查环境变量...${NC}"

    if [ -f ".env" ]; then
        echo -e "${GREEN}✓ .env 文件存在${NC}"

        # 检查关键变量
        if grep -q "DEEPSEEK_API_KEY=" .env || grep -q "ZHIPU_API_KEY=" .env; then
            echo -e "${GREEN}✓ API Key 已配置${NC}"
        else
            echo -e "${YELLOW}⚠ 未找到 API Key 配置${NC}"
        fi
    else
        echo -e "${RED}✗ .env 文件不存在${NC}"
        echo "请创建 .env 文件并配置必要的环境变量"
        exit 1
    fi
    echo ""
}

# 步骤 5: 启动服务
start_services() {
    echo -e "${YELLOW}[步骤 5/5] 启动服务...${NC}"
    echo ""

    cd docker
    docker-compose -f docker-compose.offline.yml up -d

    echo ""
    echo -e "${GREEN}======================================"
    echo "  服务启动完成！"
    echo "======================================${NC}"
    echo ""
    echo "服务访问地址："
    echo "  前端: http://localhost:3001"
    echo "  后端: http://localhost:8081/docs"
    echo "  检测: http://localhost:8001/docs"
    echo "  规划: http://localhost:8003/docs"
    echo ""
    echo "查看日志："
    echo "  cd docker && docker-compose -f docker-compose.offline.yml logs -f"
    echo ""
    echo "停止服务："
    echo "  cd docker && docker-compose -f docker-compose.offline.yml down"
    echo ""
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}停止服务...${NC}"
    cd docker
    docker-compose -f docker-compose.offline.yml down
    echo -e "${GREEN}✓ 服务已停止${NC}"
}

# 导出镜像（在开发机上运行）
export_images() {
    echo -e "${YELLOW}导出镜像到文件...${NC}"

    echo "正在构建镜像（如果尚未构建）..."
    cd ..
    docker-compose -f docker/docker-compose.yml build

    echo "正在导出镜像..."
    docker save -o ruralbrain-images.tar \
        ruralbrain-backend:latest \
        ruralbrain-detection:latest \
        ruralbrain-planning:latest

    echo "压缩镜像文件..."
    gzip -f ruralbrain-images.tar

    echo -e "${GREEN}✓ 镜像已导出到: ruralbrain-images.tar.gz${NC}"
    echo "文件大小: $(du -h ruralbrain-images.tar.gz | cut -f1)"
}

# 主菜单
show_menu() {
    echo "请选择操作："
    echo "  1) 部署应用（在目标机器上运行）"
    echo "  2) 停止服务"
    echo "  3) 导出镜像（在开发机上运行）"
    echo "  4) 退出"
    echo ""
    read -p "请输入选项 (1-4): " choice

    case $choice in
        1)
            prepare_frontend
            check_images
            check_knowledge_base
            check_env
            start_services
            ;;
        2)
            stop_services
            ;;
        3)
            export_images
            ;;
        4)
            echo "退出"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选项${NC}"
            exit 1
            ;;
    esac
}

# 主入口
main() {
    if ! command_exists docker; then
        echo -e "${RED}✗ 未安装 Docker${NC}"
        exit 1
    fi

    if ! command_exists docker-compose; then
        echo -e "${RED}✗ 未安装 docker-compose${NC}"
        exit 1
    fi

    show_menu
}

main

#!/bin/bash
# RuralBrain 轻量级镜像快速构建脚本
# 使用 ONNX Runtime，减少依赖和镜像体积

set -e

echo "=================================="
echo "RuralBrain 轻量级镜像构建工具"
echo "=================================="
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker 未运行，请先启动 Docker"
    exit 1
fi

# 定义镜像列表
declare -A images=(
    ["detection-service"]="Dockerfile.detection.onnx"
    # ["planning-service"]="Dockerfile.planning.onnx"  # 已废弃（RAG 已集成到主 Agent）
    ["backend"]="Dockerfile.backend.onnx"
    ["frontend"]="Dockerfile.frontend.onnx"
)

# 构建顺序（按依赖关系）
order=("detection-service" "backend" "frontend")

echo "构建顺序: ${order[*]}"
echo ""

# 逐个构建镜像
for service in "${order[@]}"; do
    dockerfile="${images[$service]}"
    echo "----------------------------------------"
    echo "正在构建: $service"
    echo "Dockerfile: docker/$dockerfile"
    echo "----------------------------------------"

    case $service in
        "frontend")
            docker build -f "docker/$dockerfile" \
                -t "ruralbrain-$service:onnx" \
                --build-arg NEXT_PUBLIC_API_URL=http://localhost:8081 \
                ./frontend
            ;;
        *)
            docker build -f "docker/$dockerfile" \
                -t "ruralbrain-$service:onnx" \
                .
            ;;
    esac

    if [ $? -eq 0 ]; then
        echo "✓ $service 构建成功"
        echo ""
    else
        echo "✗ $service 构建失败"
        exit 1
    fi
done

echo "=================================="
echo "所有镜像构建完成!"
echo "=================================="
echo ""
echo "查看构建的镜像:"
docker images | grep "ruralbrain.*onnx"

echo ""
echo "镜像大小统计:"
for service in "${order[@]}"; do
    size=$(docker images "ruralbrain-$service:onnx" --format "{{.Size}}")
    echo "  - $service: $size"
done

echo ""
echo "下一步:"
echo "  1. 启动服务: docker-compose -f docker-compose.onnx.yml up -d"
echo "  2. 查看日志: docker-compose -f docker-compose.onnx.yml logs -f"
echo "  3. 访问前端: http://localhost:3001"

#!/bin/bash
# ============================================================================
# RuralBrain 知识库迁移脚本
# ============================================================================
# 功能：从 bind mount 迁移到 Docker Volume
# 用法：./migrate_to_volume.sh
# ============================================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
VOLUME_NAME="ruralbrain-knowledge-base"
LOCAL_KB_DIR="./knowledge_base"
BACKUP_FILE="./backups/knowledge_base/migration_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker
check_docker() {
    if ! docker info &> /dev/null; then
        log_error "Docker 未运行"
        exit 1
    fi
}

# 检查本地知识库
check_local_kb() {
    if [ ! -d "${LOCAL_KB_DIR}" ]; then
        log_warning "本地知识库目录不存在: ${LOCAL_KB_DIR}"
        return 1
    fi

    # 检查是否为空目录
    if [ -z "$(ls -A ${LOCAL_KB_DIR})" ]; then
        log_warning "本地知识库目录为空"
        return 1
    fi

    return 0
}

# 主迁移流程
main() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  RuralBrain 知识库迁移工具${NC}"
    echo -e "${GREEN}  bind mount → Docker Volume${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    check_docker

    # 1. 检查本地知识库
    log_info "检查本地知识库..."
    if check_local_kb; then
        local kb_size=$(du -sh ${LOCAL_KB_DIR} 2>/dev/null | cut -f1)
        log_success "找到本地知识库: ${LOCAL_KB_DIR} (${kb_size})"
    else
        log_warning "未找到本地知识库，将初始化空 Volume"
        read -p "是否继续？[y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "操作已取消"
            exit 0
        fi
    fi
    echo ""

    # 2. 检查 Volume 是否已存在
    log_info "检查 Docker Volume..."
    if docker volume ls -q | grep -q "^${VOLUME_NAME}$"; then
        log_warning "Volume '${VOLUME_NAME}' 已存在"
        echo ""
        echo "请选择操作："
        echo "  1) 使用现有 Volume（跳过迁移）"
        echo "  2) 删除并重新创建 Volume"
        echo "  3) 取消操作"
        read -p "请选择 [1-3]: " choice
        case "${choice}" in
            1)
                log_info "使用现有 Volume，跳过迁移"
                exit 0
                ;;
            2)
                log_warning "删除现有 Volume..."
                docker volume rm "${VOLUME_NAME}"
                ;;
            3)
                log_info "操作已取消"
                exit 0
                ;;
            *)
                log_error "无效选择"
                exit 1
                ;;
        esac
    fi
    echo ""

    # 3. 创建备份
    if check_local_kb; then
        log_info "创建备份..."
        mkdir -p ./backups/knowledge_base
        tar czf "${BACKUP_FILE}" -C ${LOCAL_KB_DIR} .
        log_success "备份创建完成: ${BACKUP_FILE}"
    fi
    echo ""

    # 4. 创建 Volume
    log_info "创建 Docker Volume..."
    docker volume create "${VOLUME_NAME}"
    log_success "Volume 创建完成"
    echo ""

    # 5. 导入数据
    if check_local_kb; then
        log_info "导入知识库数据到 Volume..."

        docker run --rm \
            -v "${VOLUME_NAME}:/data" \
            -v "$(pwd)/${LOCAL_KB_DIR}:/import:ro" \
            alpine:latest \
            sh -c "cp -a /import/. /data/"

        log_success "数据导入完成"
    else
        log_info "创建空目录结构..."
        docker run --rm \
            -v "${VOLUME_NAME}:/data" \
            alpine:latest \
            mkdir -p /data/chroma_db
        log_success "空 Volume 初始化完成"
    fi
    echo ""

    # 6. 验证
    log_info "验证 Volume 内容..."
    local volume_size=$(docker run --rm \
        -v "${VOLUME_NAME}:/data" \
        alpine:latest \
        du -sh /data 2>/dev/null | cut -f1)
    log_success "Volume 大小: ${volume_size}"

    echo ""
    echo -e "${GREEN}========================================${NC}"
    log_success "迁移完成！"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    # 7. 后续步骤
    log_info "后续步骤："
    echo ""
    echo "1. 更新后的 docker-compose 文件已使用 Volume"
    echo "2. 重启服务以使用新 Volume："
    echo "   ${YELLOW}docker-compose -f docker-compose.dev.yml down${NC}"
    echo "   ${YELLOW}docker-compose -f docker-compose.dev.yml up -d${NC}"
    echo ""
    echo "3. 验证服务正常后，可以删除旧的 bind mount 目录："
    echo "   ${YELLOW}mv knowledge_base knowledge_base.old${NC}"
    echo ""
    echo "4. 知识库管理命令："
    echo "   ${YELLOW}./scripts/deploy/knowledge_base.sh status${NC}   # 查看状态"
    echo "   ${YELLOW}./scripts/deploy/knowledge_base.sh backup${NC}   # 备份"
    echo "   ${YELLOW}./scripts/deploy/knowledge_base.sh export${NC}    # 导出"
}

main "$@"

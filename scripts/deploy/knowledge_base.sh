#!/bin/bash
# ============================================================================
# RuralBrain 知识库管理脚本
# ============================================================================
# 功能：备份、恢复、导入、导出知识库数据
# 用法：
#   ./knowledge_base.sh backup     # 备份知识库到 tar.gz
#   ./knowledge_base.sh restore    # 从 tar.gz 恢复知识库
#   ./knowledge_base.sh export     # 导出知识库到本地目录
#   ./knowledge_base.sh import     # 从本地目录导入知识库
#   ./knowledge_base.sh init       # 初始化空知识库
#   ./knowledge_base.sh status     # 查看知识库状态
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
VOLUME_NAME="ruralbrain-knowledge-base"
BACKUP_DIR="./backups/knowledge_base"
LOCAL_KB_DIR="./knowledge_base"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/knowledge_base_${TIMESTAMP}.tar.gz"

# 容器名称（用于数据传输）
# 注意：RAG 已集成到主 Agent，此脚本保留用于兼容性
CONTAINER_NAME="ruralbrain-backend"

# ============================================================================
# 辅助函数
# ============================================================================

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

# 检查 Docker 是否运行
check_docker() {
    if ! docker info &> /dev/null; then
        log_error "Docker 未运行，请先启动 Docker"
        exit 1
    fi
}

# 检查 volume 是否存在
check_volume() {
    if docker volume ls -q | grep -q "^${VOLUME_NAME}$"; then
        return 0
    else
        return 1
    fi
}

# 检查容器是否运行
check_container() {
    if docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
        return 0
    else
        return 1
    fi
}

# 创建备份目录
ensure_backup_dir() {
    mkdir -p "${BACKUP_DIR}"
    log_info "备份目录: ${BACKUP_DIR}"
}

# 使用临时容器访问 volume
run_in_volume() {
    local command=$1
    docker run --rm \
        -v "${VOLUME_NAME}:/data" \
        alpine:latest \
        sh -c "${command}"
}

# ============================================================================
# 命令实现
# ============================================================================

# 备份知识库
cmd_backup() {
    log_info "开始备份知识库..."

    check_docker

    if ! check_volume; then
        log_error "Volume '${VOLUME_NAME}' 不存在"
        log_info "请先运行: ./knowledge_base.sh init"
        exit 1
    fi

    ensure_backup_dir

    # 使用临时容器创建备份
    log_info "正在打包知识库数据..."
    docker run --rm \
        -v "${VOLUME_NAME}:/data:ro" \
        -v "$(pwd)/${BACKUP_DIR}:/backup" \
        alpine:latest \
        tar czf "/backup/$(basename ${BACKUP_FILE})" -C /data .

    log_success "备份完成: ${BACKUP_FILE}"

    # 显示备份大小
    local size=$(du -h "${BACKUP_FILE}" | cut -f1)
    log_info "备份大小: ${size}"
}

# 恢复知识库
cmd_restore() {
    local backup_file=$1

    if [ -z "${backup_file}" ]; then
        # 使用最新的备份
        backup_file=$(ls -t ${BACKUP_DIR}/knowledge_base_*.tar.gz 2>/dev/null | head -1)
        if [ -z "${backup_file}" ]; then
            log_error "未找到备份文件"
            exit 1
        fi
        log_info "使用最新备份: ${backup_file}"
    fi

    if [ ! -f "${backup_file}" ]; then
        log_error "备份文件不存在: ${backup_file}"
        exit 1
    fi

    log_warning "此操作将覆盖现有知识库数据！"
    read -p "确认继续？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        exit 0
    fi

    log_info "开始恢复知识库..."

    check_docker

    if ! check_volume; then
        log_warning "Volume '${VOLUME_NAME}' 不存在，将自动创建"
        docker volume create "${VOLUME_NAME}"
    fi

    # 清空目标目录
    log_info "清空现有数据..."
    run_in_volume "rm -rf /data/*"

    # 解压备份
    log_info "正在解压备份..."
    local backup_basename=$(basename "${backup_file}")
    docker run --rm \
        -v "${VOLUME_NAME}:/data" \
        -v "$(dirname $(realpath ${backup_file})):/backup:ro" \
        alpine:latest \
        tar xzf "/backup/${backup_basename}" -C /data

    log_success "恢复完成"
}

# 导出知识库到本地目录
cmd_export() {
    local target_dir=$1

    if [ -z "${target_dir}" ]; then
        target_dir="${LOCAL_KB_DIR}"
    fi

    log_info "导出知识库到: ${target_dir}"

    check_docker

    if ! check_volume; then
        log_error "Volume '${VOLUME_NAME}' 不存在"
        exit 1
    fi

    # 创建目标目录
    mkdir -p "${target_dir}"

    # 使用临时容器复制数据
    log_info "正在复制数据..."
    docker run --rm \
        -v "${VOLUME_NAME}:/data:ro" \
        -v "$(pwd)/${target_dir}:/export" \
        alpine:latest \
        sh -c "cp -a /data/. /export/"

    log_success "导出完成: ${target_dir}"
}

# 从本地目录导入知识库
cmd_import() {
    local source_dir=$1

    if [ -z "${source_dir}" ]; then
        source_dir="${LOCAL_KB_DIR}"
    fi

    if [ ! -d "${source_dir}" ]; then
        log_error "源目录不存在: ${source_dir}"
        exit 1
    fi

    log_warning "此操作将覆盖现有知识库数据！"
    read -p "确认从 ${source_dir} 导入？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        exit 0
    fi

    log_info "开始导入知识库..."

    check_docker

    if ! check_volume; then
        log_warning "Volume '${VOLUME_NAME}' 不存在，将自动创建"
        docker volume create "${VOLUME_NAME}"
    fi

    # 清空目标目录
    log_info "清空现有数据..."
    run_in_volume "rm -rf /data/*"

    # 复制数据
    log_info "正在复制数据..."
    docker run --rm \
        -v "${VOLUME_NAME}:/data" \
        -v "$(pwd)/${source_dir}:/import:ro" \
        alpine:latest \
        sh -c "cp -a /import/. /data/"

    log_success "导入完成"
}

# 初始化空知识库
cmd_init() {
    log_info "初始化知识库 Volume..."

    check_docker

    if check_volume; then
        log_warning "Volume '${VOLUME_NAME}' 已存在"
        read -p "是否重新初始化？[y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "操作已取消"
            exit 0
        fi
        docker volume rm "${VOLUME_NAME}"
    fi

    docker volume create "${VOLUME_NAME}"
    log_success "Volume '${VOLUME_NAME}' 创建成功"

    # 创建基础目录结构
    run_in_volume "mkdir -p /data/chroma_db"

    log_success "知识库初始化完成"
    log_info "提示：请运行 ./knowledge_base.sh import <目录> 导入数据"
}

# 查看知识库状态
cmd_status() {
    log_info "知识库状态"
    echo "================================"

    check_docker

    # Volume 信息
    if check_volume; then
        log_success "Volume: ${VOLUME_NAME} (存在)"

        # 获取 Volume 详情
        local volume_info=$(docker volume inspect "${VOLUME_NAME}" 2>/dev/null)
        local mount_point=$(echo "${volume_info}" | grep -o '"Mountpoint": "[^"]*"' | cut -d'"' -f4)
        log_info "挂载点: ${mount_point}"

        # 获取大小（需要使用临时容器）
        local size=$(run_in_volume "du -sh /data 2>/dev/null | cut -f1" || echo "未知")
        log_info "数据大小: ${size}"

        # 显示目录结构
        echo ""
        log_info "目录结构:"
        run_in_volume "ls -lh /data" || true
    else
        log_warning "Volume: ${VOLUME_NAME} (不存在)"
        log_info "请运行: ./knowledge_base.sh init"
    fi

    echo ""
    log_info "容器状态:"
    if check_container; then
        log_success "容器 '${CONTAINER_NAME}' 正在运行"
    else
        log_warning "容器 '${CONTAINER_NAME}' 未运行"
    fi

    echo ""
    log_info "本地备份:"
    if [ -d "${BACKUP_DIR}" ]; then
        local count=$(ls -1 ${BACKUP_DIR}/knowledge_base_*.tar.gz 2>/dev/null | wc -l)
        log_info "备份文件数量: ${count}"
        if [ ${count} -gt 0 ]; then
            log_info "最新备份:"
            ls -th ${BACKUP_DIR}/knowledge_base_*.tar.gz 2>/dev/null | head -1
        fi
    else
        log_info "无备份目录"
    fi
}

# 显示帮助信息
cmd_help() {
    cat << EOF
${GREEN}RuralBrain 知识库管理脚本${NC}

${YELLOW}用法:${NC}
  $0 <command> [arguments]

${YELLOW}命令:${NC}
  ${GREEN}backup${NC}     [file]    备份知识库到 tar.gz 文件
  ${GREEN}restore${NC}    [file]    从 tar.gz 文件恢复知识库（默认使用最新备份）
  ${GREEN}export${NC}     [dir]     导出知识库到本地目录（默认: ./knowledge_base）
  ${GREEN}import${NC}     [dir]     从本地目录导入知识库（默认: ./knowledge_base）
  ${GREEN}init${NC}                 初始化空知识库 Volume
  ${GREEN}status${NC}               查看知识库状态

${YELLOW}示例:${NC}
  $0 backup                          # 备份知识库
  $0 restore                         # 恢复最新备份
  $0 restore backups/kb_20250101.tar.gz  # 恢复指定备份
  $0 export ./my_kb                  # 导出到指定目录
  $0 import ./my_kb                  # 从指定目录导入

${YELLOW}Volume 名称:${NC} ${VOLUME_NAME}
${YELLOW}备份目录:${NC} ${BACKUP_DIR}

EOF
}

# ============================================================================
# 主程序
# ============================================================================

main() {
    local command=$1
    shift || true

    case "${command}" in
        backup)
            cmd_backup "$@"
            ;;
        restore)
            cmd_restore "$@"
            ;;
        export)
            cmd_export "$@"
            ;;
        import)
            cmd_import "$@"
            ;;
        init)
            cmd_init
            ;;
        status)
            cmd_status
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            log_error "未知命令: ${command}"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"

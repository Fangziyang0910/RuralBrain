# RuralBrain 部署架构优化工作纪要

**时间**: 2026-01-21
**工作范围**: Docker 开发环境搭建 + 三合一检测服务架构

---

## 一、工作概述

完成了 RuralBrain 项目的 Docker 化部署架构优化，主要包含：

1. **开发环境 Docker 化** - 创建 `deploy/dev/` 目录，实现所有服务的热重载功能
2. **三合一检测服务架构** - 整合三个独立检测服务为统一容器，降低部署复杂度

---

## 二、开发环境配置（deploy/dev/）

### 2.1 目录结构

```
deploy/dev/
├── docker-compose.dev.yml    # 开发环境编排配置
├── Dockerfile.backend        # 后端开发镜像
├── Dockerfile.planning       # 规划服务开发镜像
├── Dockerfile.detector       # 检测服务开发镜像
├── scripts/
│   ├── dev-start.sh          # 一键启动脚本
│   └── dev-stop.sh           # 一键停止脚本
└── README.md                 # 使用指南
```

### 2.2 服务配置

| 服务 | 端口 | 热重载方式 |
|------|------|-----------|
| 前端 | 3000 | `next dev` |
| 后端 | 8080 | `uvicorn --reload` |
| 检测服务 | 8001, 8081, 8002 | `uvicorn --reload` |
| 规划服务 | 8003 | `uvicorn --reload` |

### 2.3 核心特性

- **Volume 挂载实现热重载**：源码目录挂载到容器，代码修改即时生效
- **使用 uv 管理依赖**：Python 服务统一使用 `uv sync`
- **环境变量注入**：通过 `.env` 文件统一配置

### 2.4 快速启动

```bash
cd deploy/dev/scripts
chmod +x dev-start.sh dev-stop.sh
./dev-start.sh
```

---

## 三、三合一检测服务（triple_detector/）

### 3.1 架构设计

将病虫害、大米、牛只三个独立检测服务合并为单个容器，通过启动脚本并行运行三个 FastAPI 应用。

**优势**：
- 降低资源占用（3 容器 → 1 容器）
- 简化部署配置（单镜像管理）
- 保持服务独立性（端口隔离）

### 3.2 文件结构

```
src/algorithms/triple_detector/
├── start_all.sh         # 生产环境启动脚本
├── start_all_dev.sh     # 开发环境启动脚本（含 --reload）
├── Dockerfile           # 三合一镜像构建文件
└── requirements.txt     # Python 依赖
```

### 3.3 启动脚本

`start_all.sh` 并行启动三个服务：
- 病虫害检测：端口 8001
- 大米检测：端口 8081
- 牛只检测：端口 8002

`start_all_dev.sh` 添加 `--reload` 参数支持开发环境热重载。

### 3.4 Dockerfile

```dockerfile
# 基于病虫害检测镜像（已包含 YOLOv8 和基础依赖）
FROM ruralbrain-pest-detector:latest

WORKDIR /app
# 复制三个检测服务代码
COPY src/algorithms/pest_detection/detector /app/pest
COPY src/algorithms/rice_detection/detector /app/rice
COPY src/algorithms/cow_detection/detector /app/cow
# 复制启动脚本
COPY src/algorithms/triple_detector/start_all.sh /app/start_all.sh
RUN chmod +x /app/start_all.sh

EXPOSE 8001 8081 8002
CMD ["/app/start_all.sh"]
```

---

## 四、新增文件清单

```
deploy/dev/
├── docker-compose.dev.yml
├── Dockerfile.backend
├── Dockerfile.planning
├── Dockerfile.detector
├── scripts/dev-start.sh
├── scripts/dev-stop.sh
└── README.md

src/algorithms/triple_detector/
├── start_all.sh
├── start_all_dev.sh
├── Dockerfile
└── requirements.txt
```

---

**相关文档**：
- [deploy/dev/README.md](../deploy/dev/README.md) - 开发环境详细指南
- [CLAUDE.md](../CLAUDE.md) - 项目主文档

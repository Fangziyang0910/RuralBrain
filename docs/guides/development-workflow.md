# RuralBrain 开发工作流指南

本文档详细说明 RuralBrain 项目的开发和测试工作流程。

---

## 目录

1. [环境准备](#1-环境准备)
2. [启动开发环境](#2-启动开发环境)
3. [热重载开发模式](#3-热重载开发模式)
4. [代码更改与测试流程](#4-代码更改与测试流程)
5. [生产环境验证](#5-生产环境验证)
6. [常见问题排查](#6-常见问题排查)
7. [CI/CD 配置参考](#7-cicd-配置参考)

---

## 1. 环境准备

### 1.1 必需软件

- **Docker** 和 **Docker Compose**
- **Git**
- **Bash** 终端（推荐使用 WSL2 或 Git Bash）

### 1.2 环境变量配置

确保项目根目录的 `.env` 文件已正确配置：

```bash
# 模型配置
MODEL_PROVIDER=deepseek  # 或 glm
DEEPSEEK_API_KEY=your_api_key_here

# Agent 配置
AGENT_VERSION=v2
```

### 1.3 服务端口说明

| 服务 | 开发环境端口 | 生产环境端口 | 说明 |
|------|-------------|-------------|------|
| 前端 | 3001 | 3001 | Next.js 应用 |
| 后端 | 8081 | 8081 | FastAPI + Agent V2 |
| 检测服务 | 8001 | 8001 | 统一检测网关 |
| 规划服务 | 8003 | 8003 | RAG 知识库服务 |

---

## 2. 启动开发环境

### 2.1 使用启动脚本（推荐）

```bash
# 启动所有服务（热重载模式）
bash scripts/dev/start_all_services.sh -d

# 查看服务状态
bash scripts/dev/check_services.sh

# 查看日志
cd docker && docker compose -f docker-compose.dev.yml logs -f
```

### 2.2 直接使用 Docker Compose

```bash
cd docker

# 启动所有服务（后台运行）
docker compose -f docker-compose.dev.yml up -d

# 查看服务状态
docker compose -f docker-compose.dev.yml ps

# 查看日志
docker compose -f docker-compose.dev.yml logs -f

# 停止服务
docker compose -f docker-compose.dev.yml down
```

### 2.3 启动单个服务

如果只需要启动特定服务：

```bash
cd docker

# 仅启动后端服务
docker compose -f docker-compose.dev.yml up -d backend

# 仅启动前端
docker compose -f docker-compose.dev.yml up -d frontend
```

---

## 3. 热重载开发模式

### 3.1 热重载工作原理

开发环境使用 Docker 卷挂载实现代码同步：

- **前端**：Next.js 开发模式，监听文件变化自动重新编译
- **后端**：Uvicorn `--reload` 模式，检测 Python 文件变化自动重启
- **检测服务**：Uvicorn `--reload` 模式
- **规划服务**：Uvicorn `--reload` 模式

### 3.2 热重载延迟

代码修改后，服务通常在 **1-3 秒** 内自动重启。

### 3.3 验证热重载

1. 修改代码文件
2. 观察容器日志：
   ```bash
   docker compose -f docker-compose.dev.yml logs -f backend
   ```
3. 看到类似输出表示重启成功：
   ```
   Reloading...
   Application startup complete.
   ```

### 3.4 热重载不生效？

如果热重载不工作：

1. 检查卷挂载是否正确
2. 重启容器：`docker compose -f docker-compose.dev.yml restart <service>`
3. 查看日志排查错误

---

## 4. 代码更改与测试流程

### 4.1 标准开发流程

```
1. 启动开发环境
   $ bash scripts/dev/start_all_services.sh -d

2. 验证服务健康
   $ bash scripts/dev/health_check.sh

3. 开发代码（自动热重载）
   - 修改文件
   - Docker 自动检测变更并重启服务（1-3秒）

4. 快速验证
   $ bash scripts/dev/health_check.sh --quick

5. 完整测试（重要功能完成后）
   $ bash scripts/dev/test_services.sh --normal
```

### 4.2 健康检查脚本

`scripts/dev/health_check.sh` 提供多种检查模式：

```bash
# 完整健康检查
bash scripts/dev/health_check.sh

# 快速检查（仅健康端点）
bash scripts/dev/health_check.sh --quick

# 详细输出
bash scripts/dev/health_check.sh --verbose

# 检查单个服务
bash scripts/dev/health_check.sh --service backend
bash scripts/dev/health_check.sh --service frontend
bash scripts/dev/health_check.sh --service detection
bash scripts/dev/health_check.sh --service planning
```

### 4.3 功能测试脚本

`scripts/dev/test_services.sh` 支持三级测试：

| 级别 | 选项 | 测试内容 | 预计时间 |
|------|------|----------|----------|
| 快速 | `--fast` | 基础连通性 + 健康检查 | < 30秒 |
| 正常 | `--normal` | 快速 + 检测服务测试 | < 2分钟 |
| 完整 | `--full` | 正常 + Agent/规划/前端 | < 5分钟 |

```bash
# 快速测试（代码修改后）
bash scripts/dev/test_services.sh --fast

# 正常测试（功能开发完成后）
bash scripts/dev/test_services.sh --normal

# 完整测试（发布前）
bash scripts/dev/test_services.sh --full

# 遇到错误继续测试
bash scripts/dev/test_services.sh --fast --continue
```

### 4.4 代码更改后的验证流程

**每次代码修改后建议流程**：

```bash
# 1. 等待热重载完成（1-3秒，自动）

# 2. 快速健康检查
bash scripts/dev/health_check.sh --quick

# 3. 运行相关功能测试
bash scripts/dev/test_services.sh --fast

# 4. 如果测试通过，继续开发
#    如果测试失败，修复问题
```

---

## 5. 生产环境验证

### 5.1 切换到生产模式

```bash
# 使用切换脚本（推荐）
bash scripts/dev/switch_to_production.sh

# 或手动切换
cd docker
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.yml up -d
```

### 5.2 生产环境测试

```bash
# 自动化生产测试脚本
bash scripts/dev/test_production.sh

# 或手动测试
cd docker
docker compose -f docker-compose.yml up -d
# 等待服务启动后
bash scripts/dev/test_services.sh --normal
```

### 5.3 切换回开发模式

```bash
# 使用切换脚本（推荐）
bash scripts/dev/switch_to_development.sh

# 或手动切换
cd docker
docker compose -f docker-compose.yml down
docker compose -f docker-compose.dev.yml up -d
```

### 5.4 部署前验证清单

在部署到生产环境前，请完成以下检查：

- [ ] 开发环境所有测试通过
- [ ] 切换到生产模式
- [ ] 生产环境健康检查通过
- [ ] 生产环境功能测试通过
- [ ] 生产环境配置验证（只读卷、健康检查）

---

## 6. 常见问题排查

### 6.1 服务启动失败

**症状**：容器无法启动或立即退出

**排查步骤**：

1. 查看容器状态：
   ```bash
   cd docker && docker compose -f docker-compose.dev.yml ps
   ```

2. 查看容器日志：
   ```bash
   docker compose -f docker-compose.dev.yml logs <service>
   ```

3. 常见原因：
   - 端口被占用：`lsof -ti :<port>` 检查端口
   - 依赖问题：重新构建镜像 `docker compose build`
   - 配置错误：检查 `.env` 文件

### 6.2 热重载不工作

**症状**：修改代码后服务没有自动重启

**排查步骤**：

1. 检查卷挂载：
   ```bash
   docker inspect <container> | grep -A 10 Mounts
   ```

2. 重启容器：
   ```bash
   docker compose -f docker-compose.dev.yml restart <service>
   ```

3. 检查文件权限（Windows 用户）：
   - 确保 Docker Desktop 有访问项目目录的权限
   - 在 Docker Desktop → Settings → Resources → File Sharing 中添加项目路径

### 6.3 服务间通信失败

**症状**：后端无法调用检测服务或规划服务

**排查步骤**：

1. 检查服务是否都在运行：
   ```bash
   bash scripts/dev/health_check.sh
   ```

2. 检查 Docker 网络：
   ```bash
   docker network inspect ruralbrain-network
   ```

3. 检查服务间连通性：
   ```bash
   docker exec ruralbrain-backend curl http://detection-service:8001/health
   docker exec ruralbrain-backend curl http://planning-service:8003/health
   ```

### 6.4 检测服务返回错误

**症状**：检测请求失败或返回不正确结果

**排查步骤**：

1. 检查检测服务健康：
   ```bash
   curl http://localhost:8001/health
   ```

2. 查看检测服务日志：
   ```bash
   docker compose -f docker-compose.dev.yml logs -f detection-service
   ```

3. 验证模型文件是否存在：
   ```bash
   docker exec ruralbrain-detection-service-dev ls -la /app/algorithms/detection/models/
   ```

---

## 7. CI/CD 配置参考

### 7.1 GitHub Actions 示例

在 `.github/workflows/test.yml` 中配置：

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: |
          cd docker
          docker compose -f docker-compose.dev.yml up -d

      - name: Wait for services
        run: |
          bash scripts/dev/health_check.sh --verbose

      - name: Run tests
        run: |
          bash scripts/dev/test_services.sh --fast

      - name: Show logs on failure
        if: failure()
        run: |
          cd docker
          docker compose -f docker-compose.dev.yml logs
```

### 7.2 Pre-commit Hook（可选）

在 `.git/hooks/pre-commit` 中添加：

```bash
#!/bin/bash
echo "运行预提交测试..."
bash scripts/dev/health_check.sh --quick
if [ $? -ne 0 ]; then
    echo "健康检查失败，请修复后再提交"
    exit 1
fi
```

安装脚本示例 (`scripts/dev/setup_git_hooks.sh`)：

```bash
#!/bin/bash
cp .githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "Pre-commit hook 已安装"
```

---

## 附录：快速参考

### 常用命令速查

```bash
# 启动服务
bash scripts/dev/start_all_services.sh -d

# 停止服务
bash scripts/dev/stop_all_services.sh

# 健康检查
bash scripts/dev/health_check.sh [--quick] [--verbose] [--service <name>]

# 功能测试
bash scripts/dev/test_services.sh [--fast|--normal|--full]

# 生产环境测试
bash scripts/dev/test_production.sh

# 切换环境
bash scripts/dev/switch_to_production.sh
bash scripts/dev/switch_to_development.sh

# 查看日志
cd docker && docker compose -f docker-compose.dev.yml logs -f

# 查看服务状态
bash scripts/dev/check_services.sh
```

### API 文档地址

| 服务 | 地址 |
|------|------|
| 后端 API | http://localhost:8081/docs |
| 检测服务 API | http://localhost:8001/docs |
| 规划服务 API | http://localhost:8003/docs |
| 前端界面 | http://localhost:3001 |

---

**最后更新**: 2026-02-07

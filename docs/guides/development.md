# RuralBrain 开发工作流指南

本文档说明 RuralBrain 项目的开发和测试工作流程。

---

## 核心原则（必读）

1. **所有开发使用 Docker 热重载模式** - 不推荐本地直接运行
2. **每次代码更改后必须验证** - 健康检查 + 功能测试
3. **重要功能完成后切换到生产模式测试** - 确保生产环境可用
4. **验证通过后才能提交代码** - 保持代码库健康

---

## 目录

1. [快速开始](#1-快速开始)
2. [热重载开发模式](#2-热重载开发模式)
3. [代码更改与验证流程](#3-代码更改与验证流程)
4. [生产环境验证](#4-生产环境验证)
5. [常见问题排查](#5-常见问题排查)

---

## 1. 快速开始

### 1.1 环境要求

- **Docker** 和 **Docker Compose**
- **Git**
- **Bash** 终端（推荐使用 WSL2 或 Git Bash）

### 1.2 环境变量配置

确保项目根目录的 `.env` 文件已正确配置：

```bash
# 模型配置
MODEL_PROVIDER=deepseek  # 或 glm
DEEPSEEK_API_KEY=your_api_key_here
```

### 1.3 首次启动（仅需一次）

```bash
# 1. 构建镜像（使用 ONNX 轻量级镜像）
bash scripts/dev/build-onnx-images.sh  # Linux/macOS
.\scripts\dev\build-onnx-images.ps1  # Windows

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 API 密钥

# 3. 启动开发环境
docker compose -f docker-compose.dev.yml up -d

# 4. 验证服务
bash scripts/dev/check.sh --quick
```

### 1.4 每日启动开发环境

```bash
# 1. 启动开发环境（热重载模式）
docker compose -f docker-compose.dev.yml up -d

# 2. 等待服务启动（约 10-20 秒）

# 3. 验证服务健康
bash scripts/dev/check.sh --quick

# 4. 开始开发
```

### 1.5 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3001 | Web 用户界面 |
| 后端 API 文档 | http://localhost:8081/docs | API 调试（包含 RAG 知识库） |
| 检测服务 API 文档 | http://localhost:8001/docs | 检测调试 |

### 1.6 常用操作

```bash
# 查看服务状态
docker compose -f docker-compose.dev.yml ps

# 查看日志（实时）
docker compose -f docker-compose.dev.yml logs -f

# 停止服务
docker compose -f docker-compose.dev.yml down

# 重启单个服务
docker compose -f docker-compose.dev.yml restart backend
```

---

## 2. 热重载开发模式

> **重要**：所有开发都应该使用 Docker 热重载模式，而不是本地直接运行。

### 2.1 热重载工作原理

开发环境使用 Docker 卷挂载实现代码同步：

```
本地代码文件 → Docker 卷 → 容器内文件 → 服务自动检测变化 → 重启服务
```

各服务的热重载机制：

| 服务 | 热重载机制 | 延迟 |
|------|----------|------|
| 前端 | Next.js 开发模式监听文件变化 | 1-2秒 |
| 后端 | Uvicorn `--reload` 模式 | 1-3秒 |
| 检测服务 | Uvicorn `--reload` 模式 | 1-3秒 |

### 2.2 验证热重载生效

代码修改后，服务通常在 **1-3 秒** 内自动重启。

修改代码文件后，验证热重载是否生效：

1. 修改代码文件
2. 查看容器日志确认重启：
   ```bash
   docker compose -f docker-compose.dev.yml logs -f backend
   ```
3. 看到类似输出表示重启成功：
   ```
   Reloading...
   Application startup complete.
   ```

---

## 3. 代码更改与验证流程

> **核心原则**：每次代码修改后必须验证

### 3.1 标准开发流程

```
1. 启动开发环境
   $ docker compose -f docker-compose.dev.yml up -d

2. 验证服务健康
   $ bash scripts/dev/check.sh --quick

3. 开发代码（自动热重载）
   - 修改文件
   - Docker 自动检测变更并重启服务（1-3秒）

4. 快速验证（每次修改后）
   $ bash scripts/dev/check.sh --quick
   $ bash scripts/dev/check.sh --test fast

5. 完整测试（功能开发完成后）
   $ bash scripts/dev/check.sh --test normal
```

### 3.2 健康检查脚本

`scripts/dev/check.sh` 提供多种检查模式：

```bash
# 完整健康检查
bash scripts/dev/check.sh --health

# 快速检查（仅健康端点）⭐ 每次修改后使用
bash scripts/dev/check.sh --quick

# 详细输出
bash scripts/dev/check.sh --health --verbose

# 检查单个服务
bash scripts/dev/check.sh --service backend
bash scripts/dev/check.sh --service frontend
bash scripts/dev/check.sh --service detection
```

### 3.3 功能测试脚本

`scripts/dev/check.sh` 支持三级测试：

| 级别 | 选项 | 测试内容 | 预计时间 | 使用场景 |
|------|------|----------|----------|----------|
| 快速 | `--fast` | 基础连通性 + 健康检查 | < 30秒 | 每次修改后 |
| 正常 | `--normal` | 快速 + 检测服务测试 | < 2分钟 | 功能开发完成后 |
| 完整 | `--full` | 正常 + Agent/规划/前端 | < 5分钟 | 发布前 |

```bash
# 快速测试（每次代码修改后）⭐
bash scripts/dev/check.sh --test fast

# 正常测试（功能开发完成后）⭐
bash scripts/dev/check.sh --test normal

# 完整测试（发布前）
bash scripts/dev/check.sh --test full

# 遇到错误继续测试
bash scripts/dev/check.sh --test fast --continue
```

### 3.4 代码更改验证流程

**每次代码修改后（必选）**：

```bash
# 1. 等待热重载完成（1-3秒，自动）

# 2. 快速健康检查
bash scripts/dev/check.sh --quick

# 3. 快速功能测试
bash scripts/dev/check.sh --test fast

# 4. 如果测试通过，继续开发
#    如果测试失败，修复问题
```

**功能开发完成后（必选）**：

```bash
# 1. 运行完整功能测试
bash scripts/dev/check.sh --test normal

# 2. 如果测试通过，切换到生产模式验证
#    如果测试失败，修复问题后重试
```

---

## 4. 生产环境验证

> **重要**：重要功能完成后必须切换到生产模式测试

### 4.1 切换到生产模式

```bash
# 使用切换脚本（推荐）
bash scripts/dev/switch_to_production.sh
```

### 4.2 生产环境测试

```bash
# 自动化生产测试脚本
bash scripts/dev/test_production.sh
```

### 4.3 切换回开发模式

```bash
# 使用切换脚本（推荐）
bash scripts/dev/switch_to_development.sh
```

### 4.4 部署前验证清单

在提交代码前，请完成以下检查：

- [ ] 开发环境快速测试通过（--fast）
- [ ] 开发环境完整测试通过（--normal）
- [ ] 切换到生产模式
- [ ] 生产环境测试通过
- [ ] 切换回开发模式（继续开发）

---

## 5. 常见问题排查

### 5.1 服务启动失败

**症状**：容器无法启动或立即退出

**排查步骤**：

1. 检查端口是否被占用：
   ```bash
   lsof -i :8081    # 后端
   lsof -i :8001    # 检测服务
   lsof -i :3001    # 前端
   ```

2. 查看容器日志：
   ```bash
   docker compose -f docker-compose.dev.yml logs <service>
   ```

3. 常见原因：
   - 端口被占用 → 关闭占用进程或修改端口
   - API Keys 未配置 → 检查 `.env` 文件
   - 依赖未安装 → 运行 `uv sync`

### 5.2 热重载不生效

**症状**：修改代码后服务没有自动重启

**排查步骤**：

1. 查看容器日志：
   ```bash
   docker compose -f docker-compose.dev.yml logs -f backend
   ```

2. 检查卷挂载：
   ```bash
   docker inspect <container> | grep -A 10 Mounts
   ```

3. 重启容器：
   ```bash
   docker compose -f docker-compose.dev.yml restart <service>
   ```

4. Windows 用户：检查 Docker Desktop 文件共享权限

### 5.3 检测服务无法连接

**症状**：后端无法调用检测服务

**解决方法**：

1. 确认检测服务网关已启动：
   ```bash
   curl http://localhost:8001/health
   ```

2. 检查 `.env` 中配置：
   ```bash
   DETECTION_SERVICE_URL=http://localhost:8001
   ```

3. 检查服务间连通性：
   ```bash
   docker exec ruralbrain-backend curl http://detection-service:8001/health
   ```

### 5.4 RAG 查询无结果

**症状**：知识库检索返回空结果

**解决方法**：

1. 确认知识库已构建：
   ```bash
   ls knowledge_base/chroma_db/
   ```

2. 重新构建知识库：
   ```bash
   uv run python scripts/dev/build_kb_auto.py
   ```

### 5.5 前端无法连接后端

**症状**：前端请求后端 API 失败

**解决方法**：

1. 检查后端服务是否启动：
   ```bash
   curl http://localhost:8081/health
   ```

2. 检查 CORS 配置（`.env` 文件）：
   ```bash
   ALLOWED_ORIGINS=http://localhost:3001
   ```

3. 检查 API Keys 是否配置正确

### 5.6 技能配置无法重新加载

**解决方法**：

技能重新加载策略由 `SKILL_RELOAD_STRATEGY` 配置控制：

| 策略 | 说明 | 使用场景 |
|------|------|----------|
| `always` | 每次请求都重新加载 | 开发环境 |
| `timed` | 按时间间隔重新加载 | 生产环境 |
| `never` | 从不自动重新加载 | 高性能环境 |

编辑 `.env` 文件：
```bash
SKILL_RELOAD_STRATEGY=always  # 或 timed, never
SKILL_RELOAD_INTERVAL=300     # 重新加载间隔（秒）
```

### 5.7 模块导入错误

**症状**：Python 模块找不到

**解决方法**：

```bash
# 同步依赖
uv sync

# 使用 uv 运行
uv run python <script>
```

### 5.8 测试失败排查

**症状**：健康检查或功能测试失败

**排查步骤**：

1. 查看详细输出：
   ```bash
   bash scripts/dev/check.sh --test fast --verbose
   ```

2. 查看服务日志：
   ```bash
   docker compose -f docker-compose.dev.yml logs -f <service>
   ```

3. 检查 API 文档：http://localhost:8081/docs

---

## 附录：快速参考

### 常用命令速查

```bash
# 启动开发环境（热重载）
docker compose -f docker-compose.dev.yml up -d

# 停止服务
docker compose -f docker-compose.dev.yml down

# 健康检查
bash scripts/dev/check.sh --health [--quick] [--verbose] [--service <name>]

# 功能测试
bash scripts/dev/check.sh --test [--fast|--normal|--full]

# 生产环境测试
bash scripts/dev/test_production.sh

# 切换环境
bash scripts/dev/switch_to_production.sh
bash scripts/dev/switch_to_development.sh

# 查看日志
docker compose -f docker-compose.dev.yml logs -f

# 查看服务状态
docker compose -f docker-compose.dev.yml ps
```

### 服务端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 3001 | Next.js 应用 |
| 后端 | 8081 | FastAPI + Agent V2（包含 RAG 知识库） |
| 检测服务 | 8001 | 统一检测网关 |

---

**最后更新**: 2026-03-27
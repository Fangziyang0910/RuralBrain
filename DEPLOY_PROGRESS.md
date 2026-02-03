# RuralBrain 部署进度记录

> **临时文件** - 不提交到 git
> 创建时间：2026-02-03

---

## 当前状态

### 已完成 ✅

1. **后端 Dockerfile 优化**
   - 文件：`docker/Dockerfile.backend`
   - 改动：精简依赖，只包含 Agent 编排需要的核心库
   - 移除：torch、ultralytics、opencv、chromadb 等重型依赖
   - 镜像大小：3.54GB → **445MB**

2. **规划服务 Dockerfile 优化**
   - 文件：`docker/Dockerfile.planning`
   - 改动：使用多阶段构建
   - 状态：Dockerfile 已更新，镜像构建中（被中断）

3. **docker-compose.deploy.yml 优化**
   - 注释掉 portal 服务（避免 3000 端口冲突）
   - 已推送到 GitHub

4. **.gitignore 优化**
   - 添加 `DEPLOY_PROGRESS.md` 到忽略列表（本文件不会被提交）

### 待完成 ⏳

1. **重新构建后端镜像**（当前开发电脑）
   ```bash
   cd /home/szh/projects/RuralBrain
   docker build -f docker/Dockerfile.backend -t zhihongsheng/rural-brain-backend:latest .
   ```

2. **构建规划服务镜像**（当前开发电脑）
   ```bash
   docker build -f docker/Dockerfile.planning -t zhihongsheng/rural-brain-planning-service:latest .
   ```
   - 预计构建时间：10-15 分钟
   - 预计镜像大小：~1.5GB（PyTorch 无法移除，但已优化构建过程）

3. **推送镜像到 Docker Hub**
   ```bash
   docker push zhihongsheng/rural-brain-backend:latest
   docker push zhihongsheng/rural-brain-planning-service:latest
   ```
   - 如果遇到权限问题，需要 `zhihongsheng` 账号操作

4. **提交代码到 GitHub**
   ```bash
   # 添加 DEPLOY_PROGRESS.md 到 .gitignore（已完成）
   git add docker/Dockerfile.backend docker/Dockerfile.planning .gitignore
   git commit -m "feat(docker): 优化后端和规划服务 Dockerfile，精简镜像体积"
   git push origin main
   ```

### 新电脑部署状态

**当前问题**：后端容器一直重启

```
rural-brain-backend   Restarting (2) 4 seconds ago
错误：/app/.venv/bin/python3: can't open file '/app/run_server.py': [Errno 2] No such file or directory
```

**原因**：容器还在用旧镜像（命令是 `uv run python run_server.py`），新镜像的命令是 `python run_server.py`

**解决方案**（镜像推送后在新电脑执行）：

```bash
cd ~/ruralbrain-deploy

# 停止并删除旧容器
docker-compose rm -f backend

# 拉取最新镜像
docker pull zhihongsheng/rural-brain-backend:latest

# 重新启动后端
docker-compose up -d backend

# 查看日志确认启动成功
docker-compose logs -f backend
```

---

## 服务状态清单

| 服务 | 端口 | 状态 | 镜像大小 | 备注 |
|------|------|------|----------|------|
| 前端 | 3001 | ✅ 运行中 | - | 正常 |
| 后端 | 8081 | ❌ 重启中 | 445MB（新）| 等待镜像推送 |
| 检测网关 | 8001 | ✅ 运行中 | - | 正常 |
| 规划服务 | 8003 | ✅ 运行中 | 3.54GB（旧）| 待优化 |

---

## 快速恢复命令

**回来后继续操作**：

1. 如果构建被中断，先完成构建：
   ```bash
   cd /home/szh/projects/RuralBrain
   docker build -f docker/Dockerfile.planning -t zhihongsheng/rural-brain-planning-service:latest .
   ```

2. 确认两个新镜像已构建：
   ```bash
   docker images | grep rural-brain
   ```

3. 推送到 Docker Hub（需要权限）：
   ```bash
   docker push zhihongsheng/rural-brain-backend:latest
   docker push zhihongsheng/rural-brain-planning-service:latest
   ```

4. 在新电脑上重新部署：
   ```bash
   cd ~/ruralbrain-deploy
   docker-compose pull backend
   docker-compose up -d --force-recreate backend
   ```

---

## 已修改的文件

- `docker/Dockerfile.backend` - 已优化，待提交
- `docker/Dockerfile.planning` - 已优化，待提交
- `docker/docker-compose.deploy.yml` - 已注释 portal，已推送
- `.gitignore` - 已添加 `DEPLOY_PROGRESS.md`

## 待提交的 Git 命令

```bash
git add docker/Dockerfile.backend docker/Dockerfile.planning .gitignore
git commit -m "feat(docker): 优化后端和规划服务 Dockerfile

- 后端：移除 torch、opencv 等重型依赖，镜像 3.5GB → 445MB
- 规划服务：使用多阶段构建优化构建过程
- .gitignore：添加 DEPLOY_PROGRESS.md

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin main
```

---

## 预计完成时间

- 后端镜像推送：~5 分钟
- 规划服务镜像构建 + 推送：~20 分钟
- 新电脑重新部署：~2 分钟

**总计**：约 30 分钟完成全部部署

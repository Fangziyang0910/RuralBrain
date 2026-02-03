# RuralBrain 部署进度记录

> **临时文件** - 不提交到 git
> 创建时间：2026-02-03
> 最后更新：2026-02-04

---

## 当前状态

### 已完成 ✅

1. **后端 Dockerfile 优化**
   - 文件：`docker/Dockerfile.backend`
   - 改动：精简依赖，只包含 Agent 编排需要的核心库
   - 移除：torch、ultralytics、opencv、chromadb 等重型依赖
   - 镜像大小：3.54GB → **445MB**
   - 镜像已构建并推送到 Docker Hub ✅

2. **规划服务 Dockerfile 优化**
   - 文件：`docker/Dockerfile.planning`
   - 改动：使用多阶段构建
   - 镜像大小：3.54GB → **3.36GB**（优化 180MB）
   - 镜像已构建并推送到 Docker Hub ✅

3. **docker-compose.deploy.yml 优化**
   - 注释掉 portal 服务（避免 3000 端口冲突）
   - 已推送到 GitHub

4. **.gitignore 优化**
   - 添加 `DEPLOY_PROGRESS.md` 到忽略列表（本文件不会被提交）

5. **Docker Hub 推送完成**
   - `zhihongsheng/rural-brain-backend:latest` ✅
   - `zhihongsheng/rural-brain-planning-service:latest` ✅

### 待完成 ⏳

1. **在新电脑上重新部署后端服务**（使用新镜像）

**在部署服务器上执行**：
```bash
cd ~/ruralbrain-deploy

# 1. 拉取最新代码
git pull origin main

# 2. 停止并删除旧容器
docker-compose -f docker-compose.deploy.yml rm -f backend

# 3. 拉取最新镜像
docker pull zhihongsheng/rural-brain-backend:latest
docker pull zhihongsheng/rural-brain-planning-service:latest

# 4. 重新启动服务
docker-compose -f docker-compose.deploy.yml up -d backend

# 5. 查看日志确认启动成功
docker-compose -f docker-compose.deploy.yml logs -f backend
```

---

## 服务状态清单

| 服务 | 端口 | 状态 | 镜像大小 | 备注 |
|------|------|------|----------|------|
| 前端 | 3001 | ✅ 运行中 | - | 正常 |
| 后端 | 8081 | ⏳ 待部署 | 445MB（新）| 镜像已推送 |
| 检测网关 | 8001 | ✅ 运行中 | - | 正常 |
| 规划服务 | 8003 | ⏳ 待部署 | 3.36GB（新）| 镜像已推送 |

---

## 快速恢复命令

**镜像已全部推送，现在需要在部署服务器上更新**：

```bash
# 在部署服务器上执行
cd ~/ruralbrain-deploy
git pull origin main
docker-compose -f docker-compose.deploy.yml pull backend planning
docker-compose -f docker-compose.deploy.yml up -d backend planning
docker-compose -f docker-compose.deploy.yml logs -f
```

---

## 已修改的文件

- `docker/Dockerfile.backend` - ✅ 已优化并推送
- `docker/Dockerfile.planning` - ✅ 已优化并推送
- `docker/docker-compose.deploy.yml` - ✅ 已注释 portal
- `.gitignore` - ✅ 已添加 `DEPLOY_PROGRESS.md`

---

## 部署完成情况

### ✅ 已完成
1. 后端镜像优化：3.54GB → 445MB
2. 规划服务镜像优化：3.54GB → 3.36GB
3. 两个镜像已推送到 Docker Hub

### ⏳ 待完成
在新电脑（部署服务器）上重新部署后端和规划服务

---

## 📋 一键部署

```bash
cd ~/ruralbrain-deploy
git pull origin main
bash scripts/deploy/update_services.sh
```

## 验证

```bash
# 查看服务状态
docker-compose -f docker-compose.deploy.yml ps

# 查看 backend 日志
docker-compose -f docker-compose.deploy.yml logs -f backend
```

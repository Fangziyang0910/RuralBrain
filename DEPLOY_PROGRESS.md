# RuralBrain 部署进度

## 方案变更 ✅

**不再重新构建 deploy 镜像**，直接使用现有的 `latest` 镜像进行部署。

## 已完成 ✅

### 1. 门户页准备
- ✅ static.zip 已解压到 `portal-static/static/`
- ✅ portal.html 已配置（brain → http://localhost:3001）

### 2. 镜像导出
- ✅ `ruralbrain-images.tar.gz` (12GB) - 已导出

包含镜像：
| 镜像 | 大小 |
|------|------|
| ruralbrain-backend:latest | 15GB |
| ruralbrain-planning-service:latest | 15GB |
| ruralbrain-pest-detector:latest | 2.8GB |
| ruralbrain-rice-detector:latest | 3.2GB |
| ruralbrain-cow-detector:latest | 2.8GB |
| ruralbrain-frontend:deploy | 235MB |

### 3. 部署配置
- ✅ `docker-compose.offline.yml` - 离线部署配置（使用 latest 镜像）
- ✅ `scripts/deploy/offline_deploy.sh` - 部署脚本（已更新镜像列表）
- ✅ `DEPLOY_GUIDE.md` - 部署指南

## 新电脑（目标机）操作

```bash
# 1. 复制文件到新电脑
# - ruralbrain-images.tar.gz
# - 项目代码

# 2. 导入镜像
gunzip -c ruralbrain-images.tar.gz | docker load

# 3. 配置环境变量
cp .env.example .env
nano .env  # 设置 API_KEY

# 4. 启动服务
docker-compose -f docker-compose.offline.yml up -d
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 门户页 | 8080 | 师兄给的导航页 |
| 前端 | 3001 | Next.js 聊天界面 |
| 后端 | 8081 | FastAPI + Agents |
| 规划 | 8003 | RAG 知识库 |

检测服务通过 Docker 网络内部通信，无需暴露端口。

---

**创建时间**: 2026-02-02
**状态**: ✅ 镜像已导出，可部署到新电脑

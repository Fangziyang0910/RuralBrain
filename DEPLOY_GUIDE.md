# RuralBrain 离线部署指南

> 使用现有 latest 镜像快速部署到新电脑

## 文件清单

部署到新电脑需要以下文件：

```
RuralBrain/
├── ruralbrain-images.tar.gz     (12GB) - Docker 镜像包
├── docker-compose.offline.yml    - 离线部署配置
├── scripts/deploy/offline_deploy.sh  - 部署脚本
├── portal-static/static/         - 门户页静态文件
├── docker/nginx.portal.conf      - 门户页 Nginx 配置
└── knowledge_base/chroma_db/     - 知识库（可选）
```

## 在新电脑上部署

### 1. 传输文件到新电脑

将 `ruralbrain-images.tar.gz` 和项目代码复制到新电脑。

### 2. 导入镜像

```bash
gunzip -c ruralbrain-images.tar.gz | docker load
```

### 3. 配置环境变量

```bash
# 复制 .env 文件
cp .env.example .env

# 编辑 .env，设置 API_KEY
nano .env
```

### 4. 启动服务

```bash
docker-compose -f docker-compose.offline.yml up -d
```

或使用部署脚本：

```bash
bash scripts/deploy/offline_deploy.sh
```

## 服务端口

| 服务 | 端口 | 访问地址 |
|------|------|----------|
| 门户页 | 8080 | http://localhost:8080 |
| 前端 | 3001 | http://localhost:3001 |
| 后端 | 8081 | http://localhost:8081/docs |
| 规划 | 8003 | http://localhost:8003/docs |

## 常用命令

```bash
# 查看服务状态
docker-compose -f docker-compose.offline.yml ps

# 查看日志
docker-compose -f docker-compose.offline.yml logs -f

# 停止服务
docker-compose -f docker-compose.offline.yml down

# 重启服务
docker-compose -f docker-compose.offline.yml restart
```

## 故障排查

### 镜像导入失败

检查镜像文件完整性：
```bash
md5sum ruralbrain-images.tar.gz
```

### 服务启动失败

检查日志：
```bash
docker-compose -f docker-compose.offline.yml logs backend
```

### API Key 配置

确保 `.env` 文件包含：
```
MODEL_PROVIDER=deepseek
API_KEY=sk-xxxxx
```

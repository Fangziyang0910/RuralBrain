# 部署进度记录

## 📋 当前状态

### ✅ 已完成
- 后端服务：已修复并推送
- 前端服务：已修复

### ❌ 待完成
1. **检测网关镜像** - 需要构建并推送
2. **规划服务知识库** - 知识库无法访问

---

## 🔧 需要执行的操作

### 1. 检测网关

开发机：
```bash
docker build -f docker/Dockerfile.detector -t zhihongsheng/rural-brain-detection-gateway:latest .
docker push zhihongsheng/rural-brain-detection-gateway:latest
```

部署服务器：
```bash
cd ~/ruralbrain-deploy
sed -i 's/pest-detector/detection-gateway/g' docker-compose.yml
docker pull zhihongsheng/rural-brain-detection-gateway:latest
docker-compose up -d --force-recreate detection-gateway
```

### 2. 规划服务知识库

先检查问题：
```bash
docker-compose exec planning-service ls /app/knowledge_base/
docker-compose logs planning-service | grep -i knowledge
```

根据结果选择：
- **如果知识库不存在** → 重新构建包含知识库的镜像
- **如果知识库存在但无法访问** → 检查 ChromaDB 配置或挂载卷

---

## 🚀 快速验证

```bash
# 测试各服务
curl http://localhost:8001/health  # 检测网关
curl http://localhost:8003/health  # 规划服务
curl http://localhost:8081/health  # 后端
curl -I http://localhost:3001      # 前端
```

---

**状态**: 检测网关和规划服务知识库需要修复

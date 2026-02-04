# 部署进度记录

## 📋 当前状态

### ✅ 已完成
- 后端服务：已修复并推送
- 前端服务：已修复
- **ASR语音识别功能** (2026-02-04)：
  - 前端镜像：`panzhaobin/rural-brain-frontend:latest`
  - 已构建并推送到Docker Hub
  - 包含Web Speech API语音识别功能

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

## 📝 ASR功能部署记录 (2026-02-04)

### 本地已完成
- ✅ Docker Hub 账号：panzhaobin
- ✅ 构建前端镜像（包含ASR功能）
- ✅ 推送镜像：`panzhaobin/rural-brain-frontend:latest`
- ✅ 更新远程部署配置：`docker/docker-compose.deploy.yml`

### 远程部署步骤（已完成 ✅）

#### 通过网易UU远程应用连接后，在远程Windows WSL中执行：

```bash
# 1. 准备部署目录
mkdir -p ~/ruralbrain-deploy
cd ~/ruralbrain-deploy

# 2. 传输更新后的docker-compose配置
# 从本地复制 docker/docker-compose.deploy.yml 到远程 ~/ruralbrain-deploy/docker-compose.yml

# 3. 添加 API 密钥配置
# 在 docker-compose.yml 的 backend 和 planning-service 环境变量中添加实际的 API 密钥

# 4. 重启所有服务
docker-compose up -d --force-recreate

# 5. 验证服务状态
docker-compose ps
docker-compose logs backend --tail=20
```

#### 部署结果
- ✅ 后端服务：启动成功，Agent V2 加载完成
- ✅ 检测网关：healthy
- ✅ 前端服务：正常运行
- ✅ 规划服务：healthy

### ASR功能测试

1. 在远程Windows电脑上打开 **Chrome** 或 **Edge** 浏览器
2. 访问 `http://localhost:3001`
3. 测试ASR功能：
   - 点击输入框旁的麦克风按钮 🎤
   - 允许麦克风权限
   - 说话，查看实时识别结果
   - 确认识别结果自动填入输入框

### ASR技术说明
- **实现方式**：纯前端，使用浏览器 Web Speech API
- **支持语言**：中文（zh-CN）
- **浏览器要求**：Chrome 或 Edge（Firefox支持有限）
- **无需后端支持**：所有处理在浏览器中完成

---

**状态**: ASR功能已完成远程部署 ✅；检测网关镜像和规划服务知识库仍需修复

---

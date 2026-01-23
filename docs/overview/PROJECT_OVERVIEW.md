# 乡村振兴大脑 - 多智能体检测系统

## 🌟 项目概述

本项目是一个基于 FastAPI + Next.js 的全栈智能检测系统，集成了农作物病害检测、大米品种识别和奶牛检测等功能。系统采用微服务架构，前端使用 Next.js 14 + TypeScript，后端使用 Python + FastAPI + LangChain/LangGraph，所有服务均支持 Docker 容器化部署。

## 🏗️ 系统架构

### 服务组件
```
RuralBrain/
├── src/agents/                    # 智能体核心逻辑
│   ├── cow_detection_agent.py     # 奶牛检测智能体
│   ├── pest_detection_agent.py    # 病虫害检测智能体
│   ├── rice_detection_agent.py    # 大米识别智能体
│   └── tools/                     # 工具函数
├── src/algorithms/                # 检测算法服务
│   ├── cow_detection/             # 奶牛检测服务
│   ├── pest_detection/            # 病虫害检测服务
│   └── rice_detection/            # 大米识别服务
├── service/                       # FastAPI 主服务
├── frontend/my-app/               # Next.js 前端应用
├── tests/resources/               # 测试资源
├── docs/                          # 项目文档
├── Dockerfile.backend             # 后端 Docker 配置
├── docker-compose.yml             # 完整服务编排配置
├── docker-compose.all.yml         # 检测服务编排配置
├── deploy_all.bat                 # 统一部署脚本 (Windows)
└── PROJECT_OVERVIEW.md            # 项目总体说明文档
```

### 技术栈
- **前端**: Next.js 14, TypeScript, Tailwind CSS, Radix UI
- **后端**: Python 3.13, FastAPI, LangChain, LangGraph
- **AI/ML**: PyTorch, Ultralytics YOLO, OpenCV
- **部署**: Docker, Docker Compose

## 🔧 服务配置

### 0. 前端应用 (Frontend)
- **服务目录**: `frontend/my-app/`
- **端口**: 3000
- **访问地址**: http://localhost:3000
- **Docker服务名**: frontend
- **主要功能**: Web 用户界面，提供检测功能交互界面

### 1. 病虫害检测服务 (Pest Detection)
- **服务目录**: `src/algorithms/pest_detection/`
- **端口**: 8001
- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health
- **预测接口**: POST http://localhost:8001/predict
- **Docker服务名**: pest-detector
- **主要功能**: 农作物病虫害识别与检测

### 2. 大米识别服务 (Rice Detection) 
- **服务目录**: `src/algorithms/rice_detection/`
- **端口**: 8081
- **API文档**: http://localhost:8081/docs
- **健康检查**: http://localhost:8081/health
- **预测接口**: POST http://localhost:8081/predict
- **Docker服务名**: rice-detector
- **主要功能**: 大米品种识别与分类（支持5种大米品种）

### 3. 奶牛检测服务 (Cow Detection)
- **服务目录**: `src/algorithms/cow_detection/`
- **端口**: 8002
- **API文档**: http://localhost:8002/docs
- **健康检查**: http://localhost:8002/health
- **预测接口**: POST http://localhost:8002/predict
- **Docker服务名**: cow-detector
- **主要功能**: 奶牛目标检测与识别

## 🚀 快速开始

### Docker 部署（推荐）

#### 环境要求
- Docker 20.10+
- Docker Compose 1.29+
- 内存: 至少8GB
- 磁盘空间: 至少10GB

#### 一键启动所有服务
使用新的 `docker-compose.yml` 配置文件启动所有服务（前端 + 后端 + 检测服务）：

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 服务访问地址
- **前端界面**: http://localhost:3000
- **后端 API**: http://localhost:8080
- **API 文档**: http://localhost:8080/docs
- **病虫害检测**: http://localhost:8001
- **大米识别**: http://localhost:8081
- **奶牛检测**: http://localhost:8002

#### 仅启动检测算法服务
如果只需要启动检测服务（不包含前后端）：

```bash
# 使用原有的配置文件
docker-compose -f docker-compose.all.yml up -d
```

### 统一部署脚本（Windows）
使用统一的构建脚本部署所有服务：

#### Windows系统
```batch
# 运行统一部署脚本
.\deploy_all.bat
```

#### 脚本功能
- ✅ 自动检查Docker环境
- ✅ 验证项目结构完整性
- ✅ 构建所有服务镜像
- ✅ 启动所有服务
- ✅ 执行健康检查
- ✅ 显示服务状态

#### 统一Docker Compose配置
使用 `docker-compose.all.yml` 文件可以同时管理所有服务：

```bash
# 启动所有服务
docker-compose -f docker-compose.all.yml up -d

# 停止所有服务
docker-compose -f docker-compose.all.yml down

# 重启所有服务
docker-compose -f docker-compose.all.yml restart

# 查看服务状态
docker-compose -f docker-compose.all.yml ps
```

### 单独部署
每个服务也可以单独部署：

```bash
# 病虫害检测服务
cd src/algorithms/pest_detection
docker-compose up -d

# 大米识别服务  
cd src/algorithms/rice_detection
docker-compose up -d

# 奶牛检测服务
cd src/algorithms/cow_detection
docker-compose up -d
```

### 部署脚本说明

#### deploy_all.bat (Windows)
该脚本提供以下功能：

1. **环境检查**: 验证Docker和Docker Compose安装
2. **项目验证**: 检查所有服务目录是否存在
3. **清理选项**: 可选择清理旧镜像
4. **并行构建**: 同时构建所有服务镜像
5. **健康检查**: 自动检测服务启动状态
6. **状态报告**: 显示各服务的运行状态和响应时间

#### 使用示例
```batch
# 在RuralBrain根目录运行
C:\Users\PC\Documents\GitHub\RuralBrain> deploy_all.bat

# 输出示例:
# 🚀 农村智能检测系统 - 统一部署脚本
# ============================================
# 📁 检查项目结构...
# ✅ 项目结构检查通过
# 🛑 停止现有服务...
# 🔨 构建所有服务...
# ✅ 构建成功
# 🚀 启动所有服务...
# ✅ 服务启动成功
# ⏳ 等待服务启动...
# 🔍 检查服务状态...
# 🐛 病虫害检测服务 (端口: 8001): 状态: 200, 响应时间: 0.123s
# 🌾 大米识别服务 (端口: 8081): 状态: 200, 响应时间: 0.156s
# 🐄 奶牛检测服务 (端口: 8002): 状态: 200, 响应时间: 0.089s
```

## 📋 服务状态检查

### 查看所有服务状态
```bash
docker-compose -f docker-compose.all.yml ps
```

### 查看服务日志
```bash
# 查看所有服务日志
docker-compose -f docker-compose.all.yml logs -f

# 查看特定服务日志
docker logs pest-detector
docker logs rice-detector
docker logs cow-detector
```

## 🧪 测试服务

### 健康检查测试
```bash
# 病虫害检测服务
curl http://localhost:8001/health

# 大米识别服务
curl http://localhost:8081/health

# 奶牛检测服务
curl http://localhost:8002/health
```

### 功能测试
每个服务目录下都有对应的测试脚本：
- `pest_detection/test/test.py`
- `rice_detection/test/test_service.py`
- `cow_detection/test/test_api.py`

## 📊 模型信息

### 病虫害检测模型
- **模型文件**: `models/best.pt`
- **类别文件**: `models/classes.txt`
- **支持类别**: 多种农作物病虫害
- **置信度阈值**: 0.5 (可配置)

### 大米识别模型
- **模型文件**: `models/weights_fl/best.pt`, `models/weights_xj/best.pt`
- **支持品种**: 
  - 糯米 (nuomi)
  - 珍珠大米 (zhenzhudami)
  - 五常糯米 (wuchangnuomi)
  - 丝苗米 (simiaomi)
  - 泰国香米 (taiguoxiangmi)

### 奶牛检测模型
- **模型文件**: `models/yolov8n.pt`
- **类别文件**: `models/classes.txt`
- **置信度阈值**: 0.5 (可配置)

## 🔧 配置选项

### Docker Compose 配置文件说明
- **[docker-compose.yml](docker-compose.yml)**: 完整服务编排
  - 包含前端 (Next.js)
  - 包含后端主服务 (FastAPI + Agents)
  - 包含所有检测算法服务
  - 适用于完整部署

- **[docker-compose.all.yml](docker-compose.all.yml)**: 检测服务编排
  - 仅包含检测算法服务
  - 适用于单独部署检测服务

### Dockerfile 说明
- **[Dockerfile.backend](Dockerfile.backend)**: 后端服务镜像
- **[frontend/my-app/Dockerfile](frontend/my-app/Dockerfile)**: 前端应用镜像
- 各检测服务目录下均有独立的 Dockerfile

### 环境变量
每个服务都支持以下环境变量：
- `LOG_LEVEL`: 日志级别 (INFO, DEBUG, ERROR)
- `PYTHONPATH`: Python路径
- `MODEL_PATH`: 模型文件路径
- `PORT`: 服务端口号
- `ENVIRONMENT`: 运行环境 (development/production)
- `NODE_ENV`: 前端环境 (development/production)

### CORS配置
所有服务默认启用CORS，允许跨域请求：
```python
allow_origins=["*"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

## 🛠️ 开发指南

### 本地开发
1. 克隆项目
2. 创建虚拟环境: `python -m venv venv`
3. 激活虚拟环境
4. 安装依赖: `pip install -r requirements.txt`
5. 运行服务: `python run.py`

### 添加新服务
1. 在 `src/algorithms/` 目录下创建新服务目录
2. 参照现有服务结构创建必要的文件
3. 配置端口（避免冲突）
4. 创建Dockerfile和docker-compose.yml
5. 更新本文档

## 📈 性能优化

### 生产环境建议
1. **GPU加速**: 如有可能，使用GPU版本的基础镜像
2. **负载均衡**: 配置Nginx反向代理
3. **资源限制**: 设置适当的内存和CPU限制
4. **监控告警**: 添加服务监控和告警机制
5. **日志管理**: 配置集中式日志收集

### Docker资源限制示例
```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
    reservations:
      memory: 2G
      cpus: '1.0'
```

## 🔒 安全建议

1. **访问控制**: 生产环境应添加身份验证
2. **HTTPS**: 使用SSL/TLS加密通信
3. **输入验证**: 严格验证用户输入
4. **模型保护**: 保护模型文件不被未授权访问
5. **网络安全**: 配置适当的网络策略

## 📚 相关文档

- [病虫害检测服务部署指南](src/algorithms/pest_detection/DOCKER_DEPLOY.md)
- [大米识别服务部署指南](src/algorithms/rice_detection/DOCKER_DEPLOY.md)
- [奶牛检测服务部署指南](src/algorithms/cow_detection/DOCKER_DEPLOY.md)
- [快速开始指南](src/algorithms/rice_detection/QUICK_START.md)

## 🆘 故障排除

### 常见问题

1. **端口冲突**: 确保每个服务使用不同的端口
2. **内存不足**: 增加Docker内存限制或减少批处理大小
3. **模型加载失败**: 检查模型文件是否存在且完整
4. **服务启动失败**: 查看Docker日志获取详细信息

### 获取帮助
- 查看服务日志: `docker-compose logs [service-name]`
- 检查服务状态: `docker-compose ps`
- 测试健康检查端点
- 验证模型文件完整性

## 📞 联系方式

如有问题，请通过以下方式联系：
- 提交Issue到项目仓库
- 查看相关文档和README文件
- 检查服务日志和错误信息

---

**最后更新**: 2025年12月16日
**版本**: v1.0.0
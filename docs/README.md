# RuralBrain 文档中心

欢迎来到 RuralBrain 项目文档中心。本文档帮助您快速找到所需信息。

---

## 快速导航

### 新手入门
- [快速开始指南](guides/getting-started.md) - 5 分钟上手
- [统一命令参考](commands.md) - 所有命令的权威文档
- [故障排查指南](guides/troubleshooting.md) - 常见问题解决

### 架构设计
- [系统架构设计](architecture/system-design.md) - 整体架构设计理念
- [V2 Agent 架构设计](architecture/v2-agent-architecture.md) - Progressive Disclosure 设计
- [微服务架构设计](architecture/microservices.md) - 微服务拆分和通信

### 重要决策
- [检测服务网关化决策](decisions/detection-gateway.md) - 为什么统一检测服务
- [Agent V2 迁移决策](decisions/agent-v2-migration.md) - V2 架构升级背景
- [端口统一决策](decisions/port-unification.md) - 端口规范说明

### 操作指南
- [开发工作流](guides/development.md) - 热重载和测试流程
- [快速开始](guides/getting-started.md) - Docker 和本地部署
- [故障排查](guides/troubleshooting.md) - 常见问题解决

### 优化计划
- [RAG 服务优化计划](plans/rag-optimization.md) - 性能提升和架构改进方案

### 项目记录
- [变更日志](CHANGELOG.md) - 功能迭代和配置变更记录

---

## 按场景查找

| 我想... | 查看文档 |
|---------|----------|
| 快速开始项目 | [快速开始指南](guides/getting-started.md) |
| 了解系统设计 | [系统架构设计](architecture/system-design.md) |
| 了解 V2 Agent | [V2 Agent 架构设计](architecture/v2-agent-architecture.md) |
| 查看所有命令 | [统一命令参考](commands.md) |
| 排查问题 | [故障排查指南](guides/troubleshooting.md) |
| 了解重要决策 | [架构决策记录](decisions/) |
| 开发调试 | [开发工作流](guides/development.md) |
| 查看优化计划 | [优化计划](plans/) |

---

## 文档结构

```
docs/
├── README.md                          # 📑 文档导航（本文件）
├── commands.md                        # ⚡ 统一命令参考（命令唯一来源）
├── CHANGELOG.md                       # 📜 项目变更日志
│
├── architecture/                      # 🏗️ 架构设计文档（设计思想）
│   ├── system-design.md               # 系统架构设计理念
│   ├── v2-agent-architecture.md       # V2 Agent 架构设计思想
│   └── microservices.md               # 微服务架构设计
│
├── decisions/                         # 💡 重要决策记录
│   ├── detection-gateway.md           # 检测服务网关化决策
│   ├── agent-v2-migration.md          # Agent V2 迁移决策
│   └── port-unification.md            # 端口统一决策
│
└── guides/                            # 📚 操作指南
    ├── getting-started.md             # 快速开始
    ├── development.md                 # 开发工作流
    └── troubleshooting.md             # 故障排查
│
└── plans/                             # 📋 优化计划
    └── rag-optimization.md            # RAG 服务优化计划
```

---

## 核心功能

### 智能检测
- **病虫害检测** - 农作物病虫害识别和防治建议
- **大米品种识别** - 大米品种识别和品质分析
- **奶牛目标检测** - 牛只识别和计数

### 智能规划
- **规划咨询** - 基于知识库的乡村规划问答
- **快速浏览** - 使用摘要快速了解文档
- **深度分析** - 完整阅读进行深度理解

### Agent 系统
- **V2 Agent** - 基于 Skills 架构的新一代 Agent
- **多模态交互** - 支持图片、文本输入
- **流式输出** - 实时返回响应结果

---

## 关键概念

### Progressive Disclosure（渐进式披露）

RuralBrain V2 Agent 的核心设计理念：

- 初始只提供技能描述，Token 消耗减少 50%+
- Agent 按需加载完整技能指导
- 模块化配置，易于扩展

详细文档：[V2 Agent 架构设计](architecture/v2-agent-architecture.md)

### 微服务架构

```
前端 (3001)
    ↓
后端主服务 (8081) - Orchestrator Agent
    ↓
    ├─→ 检测服务网关 (8001)
    │   ├─ /detection/pest (病虫害)
    │   ├─ /detection/rice (大米)
    │   └─ /detection/cow (奶牛)
    └─→ 规划服务 (8003)
```

详细文档：[微服务架构设计](architecture/microservices.md)

---

## 常见问题

### Q: 服务启动失败？

检查端口占用、环境变量配置、API Keys 是否正确。

详细解决方案：[故障排查指南](guides/troubleshooting.md)

### Q: 如何切换 AI 模型？

编辑 `.env` 文件，修改 `MODEL_PROVIDER`：
```bash
MODEL_PROVIDER=deepseek  # 或 glm
```

### Q: Docker 部署和本地开发如何选择？

- **Docker 部署**：适合快速体验、生产环境
- **本地开发**：适合代码修改、功能开发

详细指南：[快速开始指南](guides/getting-started.md)

---

## 相关资源

### 项目链接
- **GitHub**: https://github.com/Fangziyang0910/RuralBrain
- **问题反馈**: https://github.com/Fangziyang0910/RuralBrain/issues

### 技术栈
- **后端**: FastAPI + LangChain + LangGraph
- **前端**: Next.js 14 + TypeScript
- **AI**: ONNX Runtime + Ultralytics YOLO
- **向量数据库**: ChromaDB

---

**最后更新**: 2026-02-22
**文档版本**: v3.3
**维护者**: RuralBrain Team

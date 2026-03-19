# RuralBrain 变更日志

本文档记录 RuralBrain 项目的重要功能迭代、架构升级和配置变更。

---

## [2026-03-19] - 前端模型选择器

### 🎯 功能增强

**用户可选模型切换**

在对话界面新增模型选择器，支持 DeepSeek、GLM-4、Qwen3.5-Plus 三种模型动态切换。

**新增内容**：
- 前端：模型选择下拉框（与知识库开关并排）
- 后端：`/models` API 返回可用模型列表
- Agent：模型选择中间件实现动态切换

**代码变更**：
| 文件 | 变更 |
|------|------|
| `src/agents/context.py` | 新增 - Agent 运行时 Context |
| `src/agents/middleware/model_selection_middleware.py` | 新增 - 模型选择中间件 |
| `src/config.py` | 修改 - 新增 `AVAILABLE_MODELS` 配置 |
| `service/server.py` | 修改 - 新增 `/models` 接口 |
| `frontend/src/app/page.tsx` | 修改 - 新增模型选择器 UI |

---

## [2026-03-11] - LangChain 标准检索器与距离度量优化

### 🎯 架构优化

**符合 LangChain 标准的自定义检索器**

实现 `BaseRetriever` 接口，提供与 LangChain 生态完全兼容的检索器。

**核心改进**：
- 新增 `src/rag/core/retriever.py` - `RuralBrainRetriever` 标准检索器
- 支持多种检索策略：similarity、mmr、similarity_score_threshold
- 评分过滤功能：自动过滤低相似度结果
- 上下文扩展：可选获取文档前后文

**距离度量配置**：
- 默认使用 `cosine` 距离（余弦距离）
- 相似度计算更直观：`similarity = 1 - distance`
- 新增 `get_chroma_collection_metadata()` 配置函数

**新增配置**：
```bash
CHROMA_DISTANCE_METRIC=cosine           # 距离度量（推荐 cosine）
RETRIEVE_SCORE_THRESHOLD=0.7            # 相似度阈值（0-1）
RETRIEVE_SEARCH_TYPE=similarity_score_threshold  # 检索策略
MMR_LAMBDA_MULT=0.7                     # MMR 多样性权重
```

### 🛠️ 代码变更

| 文件 | 变更 |
|------|------|
| `src/rag/core/retriever.py` | 新增 - 标准检索器实现 |
| `src/rag/config.py` | 修改 - 新增距离度量和检索策略配置 |
| `src/rag/core/cache.py` | 修改 - 新增 `get_retriever()` 方法 |
| `src/rag/core/tools.py` | 修改 - 支持多种检索策略 |
| `src/rag/service/api/routes.py` | 修改 - 使用 cosine 距离配置 |

### ✅ 测试更新

- 新增 `tests/unit/test_rag_retriever.py` - 完整单元测试（7 个测试用例）
- 测试覆盖：检索器创建、自定义配置、检索策略、评分过滤、MMR、缓存集成

---

## [2026-03-01] - 工具生命周期 TTL 管理系统

### 🎯 架构优化

**工具自适应生命周期管理（TTL）**

实现工具 TTL（Time To Live）机制：闲置工具自动卸载，活跃工具自动续期。

**核心改进**：
- 新增 `src/agents/middleware/tool_lifecycle.py` - TTL 核心模块
- DynamicToolMiddleware 集成 TTL 机制（轮次衰减、使用续期、自动卸载）
- 支持关键工具"钉住"（永不卸载）
- 配置驱动：环境变量 + 技能 YAML 配置

**TTL 机制**：
1. 工具注册时赋予初始 TTL（默认 3 轮）
2. 每轮对话所有工具 TTL - 1
3. 工具被调用时续期（base_ttl + extension）
4. TTL 过期自动移除，钉住工具永不卸载

**新增配置**：
```bash
DEFAULT_TOOL_TTL=3          # 工具默认生命周期（轮数）
DEFAULT_TOOL_EXTENSION=2    # 续期增量（轮数）
ENABLE_TOOL_TTL=true        # 是否启用 TTL
```

### 🛠️ 测试更新

- 新增 `tests/unit/test_tool_lifecycle.py`
- 新增 `tests/integration/test_tool_ttl_integration.py`
- 新增 `tests/integration/test_tool_ttl_scenarios.py`

### 📝 代码优化

- 简化工具注册代码，消除 `ENABLE_TOOL_TTL` 分支重复
- 修复工具注册时 `last_used_round` 初始值错误
- 修复 TTL 禁用时 `_unregister_tool` 的 `AttributeError`

---

## [2026-02-27] - 知识库开关控制优化

### 🎯 架构优化

**知识库开关控制优化**

通过 config 传递布尔值，而非消息指令，简化系统逻辑。

**核心改进**：
- ✅ `load_skill` 内部处理知识库开关：规划技能保持统一接口
  - 开启（True）：注册 RAG 检索工具供 Agent 调用
  - 关闭（False）：不注册 RAG 工具，Agent 用通用知识回答
  - 未设置（None）：默认行为，注册 RAG 工具
- ✅ 简化系统提示词，移除消息指令解析逻辑
- ✅ 清理 Docker 配置：移除规划服务容器和相关引用

---

## [2026-02] - RAG 知识库集成重构

### 🎯 架构优化

**RAG 知识库从独立服务重构为 Skill 集成**

- ✅ RAG 知识库从独立服务（8003 端口）重构为 Skill 集成到主 Agent
- ✅ 规划技能 `planning.yaml` 直接引用 RAG 检索工具
- ✅ 移除服务层 `/chat/planning` 转发逻辑，统一到 `/chat/stream`
- ✅ 移除 Docker 中的 `planning-service` 容器
- ✅ 前端新增"知识库"开关，控制 RAG 工具可用性
- ✅ 更新 `orchestrator_agent_v2.py` 系统提示词支持知识库开关
- ✅ 更新 `service/schemas.py` 新增 `enable_knowledge_base` 参数

---

## [2026-02-22] - 动态工具注册与测试优化

### 🎯 架构优化

**动态工具注册系统**

实现基于会话的动态工具注册机制，确保工具调用的会话隔离和安全性。

**核心改进**：
- ✅ 新增 `DynamicToolMiddleware` - 会话隔离的动态工具注册
- ✅ 移除 `ModeAwareMiddleware` 和 `ToolSelectorMiddleware`（冗余中间件）
- ✅ 修复工具参数传递问题
- ✅ 修复异步上下文中的协程错误
- ✅ 实现严格渐进式披露架构

**代码变更**：
- 新增 `src/agents/middleware/dynamic_tool_middleware.py`
- 更新 `src/agents/middleware/skill_middleware.py` - 简化并优化
- 移除 `src/agents/middleware/mode_aware_middleware.py`
- 移除 `src/agents/middleware/tool_selector_middleware.py`

### 🔧 脚本优化

**统一检查脚本**

将多个分散的开发脚本合并为统一的 `check.sh`，提供健康检查和功能测试的一站式解决方案。

**核心改进**：
- ✅ 合并 `health_check.sh`、`test_services.sh`、`quick_start.sh` 为 `check.sh`
- ✅ 支持分级测试（fast、normal、full）
- ✅ 统一的健康检查和功能测试入口
- ✅ 改进测试输出格式和错误处理

**新脚本用法**：
```bash
# 健康检查
bash scripts/dev/check.sh --health
bash scripts/dev/check.sh --quick

# 功能测试
bash scripts/dev/check.sh --test fast
bash scripts/dev/check.sh --test normal
bash scripts/dev/check.sh --test full
```

**删除的脚本**：
- `scripts/dev/health_check.sh`
- `scripts/dev/test_services.sh`
- `scripts/dev/quick_start.sh`

### 🛠️ 测试更新

**测试架构优化**

- ✅ 更新测试以适应严格渐进式披露架构
- ✅ 添加 `SkillMiddleware` 单元测试
- ✅ 修复测试函数参数顺序

### 📝 文档更新

- ✅ 更新开发工作流文档
- ✅ 更新命令参考文档
- ✅ 更新故障排查指南

---

## [2026-02] - Skills 架构优化（YAML 配置驱动）

### 🎯 架构优化

**技能配置迁移到 YAML**

将技能定义从 Python 代码迁移到 YAML 配置文件，进一步提高可维护性和扩展性。

**核心改进**：
- ✅ 技能配置与代码完全分离
- ✅ 新增技能注册中心（`registry.py`）
- ✅ 支持技能热重载（可配置策略）
- ✅ Skill 数据模型简化（Pydantic BaseModel）
- ✅ 移除 V1/V2 版本切换逻辑，统一使用 V2 架构

**代码精简**：
- 删除 8 个技能实现文件（`*_skills.py`）
- 新增 6 个 YAML 配置文件
- 删除 `mode_aware_middleware.py`（冗余中间件）
- 总代码行数减少 ~1000 行

**新增配置**：
```bash
# 技能重新加载策略
SKILL_RELOAD_STRATEGY=always  # always | timed | never
SKILL_RELOAD_INTERVAL=300     # 重新加载间隔（秒）
```

**目录结构变更**：
```
src/agents/skills/
├── configs/              # 新增：YAML 配置目录
│   ├── detection.yaml
│   ├── planning.yaml
│   └── ...
├── registry.py           # 新增：技能注册中心
├── base.py               # 简化：Pydantic BaseModel
└── __init__.py
```

---

## [2026-01] - V2 Agent 架构升级

### 🎯 架构升级

**V2 Agent Skills 架构**

基于 LangChain 官方 Skills 模式和 Progressive Disclosure 最佳实践，完成 Agent 架构升级。

**核心改进**：
- ✅ 提示词长度从 82 行减少到 20 行（减少 75%）
- ✅ Token 消耗减少 50%+（按需加载技能）
- ✅ 模块化技能配置，易于扩展
- ✅ 支持版本切换（V1/V2）和自动降级

**新增功能**：
- `SkillMiddleware` - 技能中间件，实现渐进式披露
- `load_skill` 工具 - Agent 可按需加载完整技能指导
- 版本切换机制 - 通过 `AGENT_VERSION` 环境变量选择

**技术实现**：
- 技能抽象层（`src/agents/skills/base.py`）
- 技能注册中心（`src/agents/skills/registry.py`）
- 三个检测技能（病虫害、大米、奶牛）
- 新旧 Agent 共存，平滑迁移

**文档**：[V2 Agent 架构详解](architecture/v2-agent-architecture.md)

---

### 🔧 配置变更

**统一检测服务端口（检测服务网关化）**

**原始配置**：
| 服务 | 原端口 | 问题 |
|------|--------|------|
| 病虫害检测 | 8000 | 独立端口 |
| 大米品种识别 | 8001 | 独立端口 |
| 奶牛检测 | 8002 | 独立端口 |

**新配置（统一网关）**：
| 服务 | 新端口 | 说明 |
**影响范围**：
- 检测服务配置已更新
- Agent 调用配置已同步更新
- Docker 配置已更新

**相关决策**：
- [端口统一决策](decisions/port-unification.md) - 端口分配规范
- [检测服务网关化决策](decisions/detection-gateway.md) - 详细技术方案

---

### 📦 部署优化

**Docker 开发环境**

- 创建 `docker/` 目录，实现所有服务的热重载
- 开发环境配置（`docker-compose.dev.yml`）
- 统一启动脚本

**检测服务网关化**

- 整合三个独立检测服务到统一网关（端口 8001）
- 降低资源占用（3 容器 → 1 容器）
- 简化部署配置（单镜像管理）
- 统一接口规范：`/detection/{type}/{action}`

**相关决策**：[检测服务网关化决策](decisions/detection-gateway.md)

---

### 🛠️ 新增功能

**多图片上传**

- 前端实现批量图片上传
- 支持同时上传多张图片进行检测
- 优化用户交互体验

**流式输出**

- 后端实现 SSE 流式返回
- 前端支持实时渲染 Agent 响应
- 提升用户体验

**模型管理系统**

- 支持多模型供应商切换（DeepSeek、智谱AI）
- 统一的 `ModelManager` 类
- 环境变量配置 `MODEL_PROVIDER`

---

### 🐛 Bug 修复

- 修复前端 API 路由问题
- 修复检测服务路径导入问题
- 修复 PPT 文档内容索引合并问题

---

## [2025-12] - 微服务架构优化

### 架构调整

**统一算法服务架构**

- 整合三个检测服务到统一的 FastAPI 应用
- 统一接口规范（`/detect` 端点）
- 标准化输入输出格式

**RAG 服务化**

- 实现服务化部署
- 添加健康检查和监控

### 新增功能

- 规划咨询智能咨询
- 知识库构建自动化
- SummarizationMiddleware（历史对话摘要）

---

## [2025-11] - 基础功能实现

### 初始版本

- 图像检测 Agent（病虫害、大米、奶牛）
- FastAPI 后端服务
- Next.js 前端界面
- 单 Agent 模式

---

## 版本说明

### 版本命名规范

- **主版本号**：重大架构升级
- **次版本号**：新功能添加
- **修订号**：Bug 修复和小的改进

### 重要里程碑

| 版本 | 日期 | 重要变更 |
|------|------|----------|
| v1.0 | 2025-11 | 初始版本，基础功能 |
| v1.5 | 2025-12 | 微服务架构，RAG 服务化 |
| v2.0 | 2026-01 | V2 Agent 架构升级 |
| v3.0 | 2026-02-11 | 文档结构重构，组件更新 |

---

## 变更类型说明

- 🎯 **架构升级**：系统架构的重大调整
- 🔧 **配置变更**：端口、环境变量等配置修改
- 📦 **部署优化**：部署流程、容器化改进
- 🛠️ **新增功能**：新功能、新特性
- ✨ **功能改进**：现有功能优化
- 🐛 **Bug 修复**：问题修复
- 📝 **文档更新**：文档增删改
- 🗑️ **废弃删除**：功能废弃或删除

---

## 相关文档

- [CLAUDE.md](../CLAUDE.md) - 项目级配置
- [系统架构设计](architecture/system-design.md) - 系统架构设计理念
- [V2 Agent 架构设计](architecture/v2-agent-architecture.md) - Progressive Disclosure 设计
- [快速开始](guides/getting-started.md) - Docker 和本地部署

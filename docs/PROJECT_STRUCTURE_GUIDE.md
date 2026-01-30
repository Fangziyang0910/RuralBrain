# RuralBrain 项目结构组织指南

> **版本**: v1.0
> **更新日期**: 2026-01-23
> **维护者**: RuralBrain 开发团队

---

## 📋 目录

- [目标](#目标)
- [核心原则](#核心原则)
- [标准目录结构](#标准目录结构)
- [文件放置规则](#文件放置规则)
- [协作者指南](#协作者指南)
- [常见问题](#常见问题)

---

## 目标

本文档旨在为 RuralBrain 项目提供一个统一的项目结构组织标准，确保：

1. **一致性**: 所有协作者遵循相同的目录结构和命名规范
2. **可维护性**: 文件分类清晰，便于查找和维护
3. **可扩展性**: 结构设计支持项目未来增长
4. **标准化**: 符合 Python/Next.js 项目最佳实践

---

## 核心原则

### 1. 根目录最小化原则

根目录只保留**必须**的配置文件和入口文件，其他文件都应归档到子目录。

```
✅ 推荐：根目录只有必要的配置文件
❌ 避免：根目录堆满测试脚本、日志文件、临时文档
```

### 2. 职责分离原则

每个目录有明确的职责范围：

| 目录 | 职责 | 不应包含 |
|------|------|----------|
| `src/` | 源代码 | 测试文件、脚本、文档 |
| `tests/` | 测试代码 | 业务逻辑代码 |
| `scripts/` | 脚本工具 | 业务逻辑代码 |
| `docs/` | 文档 | 代码、配置文件 |
| `deploy/` | 部署配置 | 业务逻辑代码 |

### 3. 按类型分类原则

文件按**类型**而非**功能**分类：

```
✅ 推荐: tests/integration/ （按类型分类）
❌ 避免: tests/pest_detection/ （按功能分类，重复）
```

### 4. 避免深层嵌套原则

目录层级不超过 3 层（特殊情况除外）：

```
✅ 推荐: src/algorithms/pest_detection/
❌ 避免: src/algorithms/detection/pest/detector/v2/
```

---

## 标准目录结构

### 完整目录树

```
RuralBrain/
├── 📄 配置文件（根目录）
│   ├── CLAUDE.md              # 项目核心指导文档
│   ├── README.md              # 项目说明文档
│   ├── .env                   # 环境变量（不提交到 Git）
│   ├── .env.example           # 环境变量模板
│   ├── pyproject.toml         # Python 项目配置
│   ├── uv.lock                # 依赖锁定文件
│   ├── docker-compose.yml     # Docker Compose 配置
│   ├── .gitignore             # Git 忽略规则
│   └── .dockerignore          # Docker 忽略规则
│
├── 📁 src/                    # 【源代码】所有业务逻辑代码
│   ├── agents/                # Agent 系统
│   │   ├── skills/            # Skills 架构
│   │   ├── middleware/        # 中间件
│   │   └── tools/             # LangChain 工具
│   ├── algorithms/            # 独立检测算法
│   │   ├── pest_detection/    # 病虫害检测
│   │   ├── rice_detection/    # 大米识别
│   │   └── cow_detection/     # 奶牛检测
│   ├── rag/                   # RAG 知识库系统
│   │   ├── core/              # 核心功能
│   │   └── utils/             # 工具函数
│   ├── utils/                 # 通用工具类
│   └── config.py              # 配置管理
│
├── 📁 service/                # 【服务层】FastAPI 主服务
│   ├── server.py              # 主服务器入口
│   └── settings.py            # 服务配置
│
├── 📁 frontend/               # 【前端】Next.js 项目
│   ├── src/                   # 源代码
│   ├── public/                # 静态资源
│   └── package.json           # 依赖配置
│
├── 📁 tests/                  # 【测试】所有测试代码
│   ├── integration/           # 集成测试
│   ├── unit/                  # 单元测试
│   └── resources/             # 测试资源数据
│
├── 📁 scripts/                # 【脚本】开发、部署、工具脚本
│   ├── dev/                   # 开发相关脚本
│   ├── deploy/                # 部署脚本
│   └── env/                   # 环境配置脚本
│
├── 📁 docs/                   # 【文档】所有项目文档
│   ├── architecture/          # 架构设计文档
│   ├── guides/                # 使用指南
│   ├── reports/               # 测试报告、优化报告
│   └── api/                   # API 文档
│
├── 📁 deploy/                 # 【部署】部署相关配置
│   ├── dev/                   # 开发环境部署
│   ├── prod/                  # 生产环境部署
│   └── docker/                # Docker 配置
│
├── 📁 knowledge_base/         # 【数据】RAG 知识库数据
├── 📁 uploads/                # 【数据】用户上传文件
├── 📁 pest_detection_results/ # 【数据】病虫害检测结果
├── 📁 cow_detection_results/  # 【数据】奶牛检测结果
├── 📁 rice_detection_results/ # 【数据】大米检测结果
└── 📁 logs/                   # 【日志】运行日志（不提交）
```

### 目录职责详解

#### 1. `src/` - 源代码目录

**用途**: 存放所有可运行的 Python 业务代码

**结构**:
```
src/
├── agents/          # Agent 相关代码
│   ├── skills/      # Skill 定义
│   ├── middleware/  # 中间件
│   └── tools/       # 工具定义
├── algorithms/      # 独立算法服务
│   └── {algorithm}/ # 每个算法一个目录
│       ├── detector/    # 检测器代码
│       ├── config.py    # 算法配置
│       └── start_service.py  # 服务启动
├── rag/             # RAG 相关代码
│   ├── core/         # 核心功能
│   ├── scripts/      # RAG 脚本（服务于 RAG）
│   └── utils/        # 工具函数
├── utils/           # 项目通用工具
└── config.py        # 全局配置
```

**放置规则**:
- ✅ 所有可被导入的 Python 模块
- ❌ 不放测试代码（放 `tests/`）
- ❌ 不放启动脚本（放 `scripts/`）

#### 2. `tests/` - 测试目录

**用途**: 存放所有测试代码和测试资源

**结构**:
```
tests/
├── integration/     # 集成测试
│   ├── test_agent_comparison.py
│   ├── test_rag_integration.py
│   └── test_user_scenario.py
├── unit/            # 单元测试
│   ├── test_config.py
│   └── test_utils.py
└── resources/       # 测试数据
    ├── images/      # 测试图片
    └── fixtures/    # 测试夹具
```

**命名规范**:
- 测试文件: `test_*.py` 或 `*_test.py`
- 测试类: `Test*`
- 测试函数: `test_*`

#### 3. `scripts/` - 脚本目录

**用途**: 存放开发、部署、工具脚本

**结构**:
```
scripts/
├── dev/             # 开发相关脚本
│   ├── build_kb_auto.py    # 知识库构建
│   ├── main.py             # 本地测试入口
│   └── debug_agent.py      # 调试脚本
├── deploy/          # 部署脚本
│   ├── start.sh            # 统一启动
│   ├── start_backend.sh    # 后端启动
│   ├── deploy_all.bat      # Windows 部署
│   └── run_frontend.bat    # 前端启动
└── env/             # 环境配置脚本
    └── claude_code_env.sh
```

**路径处理原则**:
所有脚本都应从项目根目录运行，脚本开头需添加：

```python
# Python 脚本
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

```bash
# Bash 脚本
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"
```

```batch
# Batch 脚本
@echo off
set SCRIPT_DIR=%~dp0
cd %SCRIPT_DIR%\..\..
```

#### 4. `docs/` - 文档目录

**用途**: 存放所有项目文档

**结构**:
```
docs/
├── architecture/    # 架构设计文档
│   ├── V2 Agent 架构详解.md
│   └── Agent架构升级方案.md
├── guides/          # 使用指南
│   ├── model_management.md
│   └── frontend_guide.md
├── reports/         # 测试报告、优化报告
│   ├── RAG_INTEGRATION_TEST_REPORT.md
│   ├── PLANNING_OPTIMIZATION_REPORT.md
│   └── 规划咨询测试报告.md
├── api/             # API 文档
└── README.md        # 文档目录说明
```

#### 5. `deploy/` - 部署目录

**用途**: 存放部署相关配置和脚本

**结构**:
```
deploy/
├── dev/             # 开发环境
│   ├── scripts/     # 开发部署脚本
│   └── docker-compose.dev.yml
├── prod/            # 生产环境
│   ├── scripts/     # 生产部署脚本
│   └── docker-compose.prod.yml
└── docker/          # Docker 配置
    ├── Dockerfile.backend
    └── Dockerfile.frontend
```

---

## 文件放置规则

### 根目录文件规范

**应保留在根目录的文件**:

| 文件 | 用途 | 是否提交 Git |
|------|------|-------------|
| `CLAUDE.md` | 项目核心指导文档 | ✅ 是 |
| `README.md` | 项目说明 | ✅ 是 |
| `run_server.py` | 主服务启动入口 | ✅ 是 |
| `.env.example` | 环境变量模板 | ✅ 是 |
| `.env` | 环境变量（含密钥） | ❌ 否 |
| `pyproject.toml` | 项目配置 | ✅ 是 |
| `uv.lock` | 依赖锁定 | ✅ 是 |
| `docker-compose*.yml` | Docker 配置 | ✅ 是 |
| `Dockerfile*` | Dockerfile | ✅ 是 |
| `.gitignore` | Git 忽略规则 | ✅ 是 |
| `.dockerignore` | Docker 忽略规则 | ✅ 是 |
| `.python-version` | Python 版本 | ✅ 是 |

**不应放在根目录的文件**:

| 文件类型 | 应放位置 | 示例 |
|---------|---------|------|
| 测试脚本 | `tests/integration/` | `test_agent_comparison.py` |
| 日志文件 | `logs/` 或忽略 | `backend.log` |
| 开发脚本 | `scripts/dev/` | `build_kb_auto.py` |
| 部署脚本 | `scripts/deploy/` | `deploy_all.bat` |
| 临时报告 | `docs/reports/` | `TEST_REPORT.md` |
| 环境脚本 | `scripts/env/` | `claude_code_env.sh` |

### 测试文件放置

**规则**: 所有测试相关文件都放在 `tests/` 目录下

```
✅ 正确:
tests/integration/test_agent_comparison.py
tests/unit/test_config.py

❌ 错误:
test_agent_comparison.py  (根目录)
src/test_agent.py         (混在源码中)
```

### 文档文件放置

**规则**: 根据文档类型分类存放

| 文档类型 | 放置位置 | 示例 |
|---------|---------|------|
| 架构设计 | `docs/architecture/` | `V2 Agent 架构详解.md` |
| 使用指南 | `docs/guides/` | `model_management.md` |
| 测试报告 | `docs/reports/` | `RAG_INTEGRATION_TEST_REPORT.md` |
| 项目概览 | `docs/project/` | `PROJECT_OVERVIEW.md` |
| API 文档 | `docs/api/` | `api_reference.md` |

### 日志文件处理

**规则**: 日志文件统一放在 `logs/` 目录，并加入 `.gitignore`

```gitignore
# .gitignore
logs/
*.log
```

### 脚本文件处理

**规则**: 根据脚本用途分类存放

| 脚本类型 | 放置位置 | 示例 |
|---------|---------|------|
| 开发辅助 | `scripts/dev/` | `build_kb_auto.py`, `debug.py` |
| 部署相关 | `scripts/deploy/` | `start.sh`, `deploy_all.bat` |
| 环境配置 | `scripts/env/` | `claude_code_env.sh` |
| 数据迁移 | `scripts/migrate/` | `migrate_kb.py` |

---

## 协作者指南

### 添加新功能时

当你需要添加新功能时，遵循以下决策树：

```
1. 是新的独立算法服务吗？
   └─ 是 → src/algorithms/{algorithm_name}/
   └─ 否 → 继续

2. 是新的 Agent 技能吗？
   └─ 是 → src/agents/skills/{skill_name}.py
   └─ 否 → 继续

3. 是测试代码吗？
   └─ 是 → tests/{unit|integration}/
   └─ 否 → 继续

4. 是文档吗？
   └─ 是 → docs/{architecture|guides|reports}/
   └─ 否 → 继续

5. 是脚本吗？
   └─ 是 → scripts/{dev|deploy|env}/
   └─ 否 → 继续

6. 是配置吗？
   └─ 是 → deploy/{env}/ 或更新现有配置
   └─ 否 → 询问团队
```

### 添加新算法服务时

目录结构模板：
```
src/algorithms/{algorithm_name}/
├── detector/             # 检测器代码
│   ├── __init__.py
│   ├── model.py          # 模型定义
│   └── predictor.py      # 预测器
├── config.py             # 算法配置
├── start_service.py      # 服务启动
├── README.md             # 算法说明
└── Dockerfile            # Docker 配置（如需要）
```

### 添加新测试时

根据测试类型选择：
- **单元测试**: `tests/unit/test_{module}.py`
- **集成测试**: `tests/integration/test_{feature}.py`
- **端到端测试**: `tests/e2e/test_{scenario}.py`

### 添加新文档时

根据文档类型选择：
- **架构设计**: `docs/architecture/{name}.md`
- **使用指南**: `docs/guides/{topic}.md`
- **测试报告**: `docs/reports/{name}_{date}.md`
- **API 文档**: `docs/api/{service}.md`

### 添加新脚本时

根据脚本用途选择：
- **开发辅助**: `scripts/dev/{name}.py`
- **部署脚本**: `scripts/deploy/{name}.{sh|bat}`
- **环境配置**: `scripts/env/{name}.sh`

---

## 命名规范

### 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| Python 模块 | `snake_case.py` | `image_detection_agent.py` |
| 测试文件 | `test_*.py` | `test_agent_comparison.py` |
| 配置文件 | `*.toml`, `*.yaml` | `pyproject.toml` |
| 脚本文件 | `snake_case.{py\|sh\|bat}` | `build_kb_auto.py` |
| 文档文件 | `Title_Case.md` 或 `中文标题.md` | `V2_Agent_架构详解.md` |

### 目录命名

- 使用 `snake_case` 或 `kebab-case`
- 使用复数形式表示集合: `tests/`, `scripts/`, `agents/`
- 使用单数形式表示模块: `src/`, `service/`

### 变量命名

- Python: `snake_case`
- 类名: `PascalCase`
- 常量: `UPPER_SNAKE_CASE`

---

## 常见问题

### Q1: 我写的脚本应该放在哪里？

**A**: 根据用途决定：
- 临时开发调试 → `scripts/dev/`
- 部署相关 → `scripts/deploy/`
- 一次性迁移 → 可以临时放根目录，完成后删除
- 长期使用的工具 → `scripts/tools/`

### Q2: 测试应该怎么组织？

**A**: 按测试层级组织：
- 单元测试：`tests/unit/`
- 集成测试：`tests/integration/`
- 端到端测试：`tests/e2e/`

### Q3: 日志文件怎么办？

**A**:
- 运行时日志：写入 `logs/` 目录
- 将 `logs/` 加入 `.gitignore`
- 如需保留日志用于调试，可归档到 `docs/reports/`

### Q4: 我需要创建一个新目录，应该叫什么名字？

**A**: 遵循以下原则：
1. 优先使用已有的目录结构
2. 使用描述性名称，避免缩写
3. 与团队确认后再创建
4. 更新本文档

### Q5: 配置文件应该放哪里？

**A**:
- 项目级配置: 根目录 (`pyproject.toml`, `.env.example`)
- 服务级配置: 各服务目录下 (`src/algorithms/*/config.py`)
- 环境特定配置: `deploy/{env}/`

### Q6: Dockerfile 应该放哪里？

**A**:
- 主要 Dockerfile: 根目录 (`Dockerfile.backend`)
- 服务特定 Dockerfile: 各服务目录下
- 开发用 Docker 配置: `deploy/docker/`

---

## 检查清单

在提交代码前，请检查：

- [ ] 测试文件放在 `tests/` 目录
- [ ] 脚本文件放在 `scripts/` 目录
- [ ] 文档放在 `docs/` 目录对应分类
- [ ] 日志文件会被 `.gitignore` 忽略
- [ ] 没有临时文件或调试文件留在根目录
- [ ] 文件命名符合规范
- [ ] 添加了必要的 `__init__.py` 文件
- [ ] 更新了相关文档（如 CLAUDE.md）

---

## 更新日志

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-01-23 | 初始版本，建立项目结构规范 | RuralBrain 团队 |

---

## 反馈与建议

如果你对本指南有疑问或建议，请：

1. 在团队会议上提出
2. 创建 Issue 讨论
3. 直接更新本文档（需要评审）

**记住**: 这是一个活文档，应该随着项目发展而演进。

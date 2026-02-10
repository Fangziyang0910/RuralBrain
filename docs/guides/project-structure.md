# RuralBrain 项目结构组织指南

> **版本**: v2.0
> **更新日期**: 2026-01-31
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
| `service/` | 主服务代码 | 测试文件、脚本 |
| `src/` | 核心业务逻辑代码 | 测试文件、配置文件 |
| `tests/` | 测试代码 | 业务逻辑代码 |
| `scripts/` | 脚本工具 | 业务逻辑代码 |
| `docs/` | 文档 | 代码、配置文件 |
| `frontend/` | 前端应用 | 后端代码 |

### 3. 按类型分类原则

文件按**类型**而非**功能**分类：

```
✅ 推荐: tests/integration/ （按类型分类）
❌ 避免: tests/pest_detection/ （按功能分类，重复）
```

### 4. 避免深层嵌套原则

目录层级不超过 3 层（特殊情况除外）：

```
✅ 推荐: src/algorithms/detection/
❌ 避免: src/algorithms/detection/services/models/pest/
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
│   ├── .gitignore             # Git 忽略规则
│   ├── run_server.py          # 后端服务启动脚本
│   ├── run_frontend.py        # 前端服务启动脚本
│   └── .gitattributes         # Git 属性配置
│
├── 📁 service/                # 【主服务】FastAPI 主服务
│   ├── server.py              # FastAPI 应用入口
│   ├── settings.py            # 服务配置
│   └── schemas.py             # 数据模型定义
│
├── 📁 src/                    # 【源代码】核心业务逻辑
│   ├── agents/                # Agent 系统
│   │   ├── orchestrator_agent_v2.py  # V2 统一编排 Agent
│   │   ├── skills/            # Skills 架构模块
│   │   │   ├── detection_skills.py     # 检测技能
│   │   │   ├── planning_skills.py      # 规划技能
│   │   │   ├── pricing_skills.py       # 定价技能
│   │   │   └── orchestration_skills.py  # 编排技能
│   │   ├── tools/             # Agent 工具集
│   │   │   ├── pest_detection_tool.py   # 病虫害检测工具
│   │   │   ├── rice_detection_tool.py   # 大米识别工具
│   │   │   ├── cow_detection_tool.py    # 奶牛检测工具
│   │   │   ├── pricing_tool.py          # 定价工具
│   │   │   ├── marketing_tool.py        # 营销工具
│   │   │   └── farm_inspection_tool.py  # 农场检查工具
│   │   └── middleware/        # 中间件系统
│   │       ├── skill_middleware.py      # 技能中间件
│   │       └── tool_selector_middleware.py  # 工具选择中间件
│   │
│   ├── algorithms/            # 检测算法服务
│   │   ├── api/               # 统一 API 网关（端口 8001）
│   │   │   └── main.py        # FastAPI 检测服务网关
│   │   └── detection/         # 检测算法实现
│   │       ├── pest_service.py      # 病虫害检测服务
│   │       ├── rice_service.py      # 大米品种识别服务
│   │       ├── cow_service.py       # 奶牛检测服务
│   │       └── models/              # YOLO 模型文件
│   │
│   ├── rag/                   # RAG 知识库系统
│   │   ├── core/              # RAG 核心功能
│   │   │   ├── tools.py       # 7 个核心检索工具
│   │   │   ├── context_manager.py  # 上下文管理
│   │   │   ├── cache.py       # 向量缓存
│   │   │   └── summarization.py    # 文档摘要
│   │   ├── service/           # RAG 服务实现
│   │   │   ├── main.py        # FastAPI 服务入口（端口 8003）
│   │   │   └── config.py      # 服务配置
│   │   └── docs/              # 知识库文档
│   │
│   ├── config.py              # 全局配置（模型管理等）
│   └── utils/                 # 工具函数
│
├── 📁 frontend/              # 【前端应用】Next.js 应用
│   ├── src/                  # 前端源代码
│   │   ├── app/              # Next.js App Router
│   │   │   ├── api/          # API 路由
│   │   │   └── page.tsx       # 主页面
│   │   ├── components/       # React 组件
│   │   │   └── ui/           # UI 组件库
│   │   └── utils/            # 前端工具函数
│   ├── package.json          # 前端依赖配置
│   ├── next.config.mjs       # Next.js 配置
│   └── tsconfig.json         # TypeScript 配置
│
├── 📁 docker/                # 【Docker 配置】
│   ├── docker-compose.yml    # 生产环境编排
│   ├── docker-compose.dev.yml # 开发环境编排（热重载）
│   ├── Dockerfile.backend    # 后端镜像
│   ├── Dockerfile.frontend   # 前端镜像
│   └── README.md             # Docker 使用说明
│
├── 📁 tests/                 # 【测试代码】
│   ├── integration/          # 集成测试
│   │   └── test_agent.py    # Agent 集成测试
│   └── unit/                 # 单元测试
│       └── test_tools.py    # 工具单元测试
│
├── 📁 scripts/               # 【脚本工具】
│   ├── dev/                  # 开发脚本
│   │   ├── build-onnx-images.ps1   # ONNX 镜像构建（Windows）
│   │   ├── build-onnx-images.sh    # ONNX 镜像构建（Linux/macOS）
│   │   ├── health_check.sh         # 健康检查脚本
│   │   ├── test_services.sh        # 分级功能测试脚本
│   │   ├── test_production.sh      # 生产环境测试脚本
│   │   ├── switch_to_production.sh # 切换到生产模式
│   │   ├── switch_to_development.sh # 切换到开发模式
│   │   ├── check_services.sh       # 检查服务状态
│   │   └── build_kb_auto.py        # 自动构建知识库
│   └── deploy/               # 部署脚本
│
├── 📁 docs/                  # 【项目文档】
│   ├── README.md             # 文档导航中心
│   ├── CHANGELOG.md          # 项目变更日志
│   ├── overview/             # 项目概览
│   │   └── PROJECT_OVERVIEW.md
│   ├── guides/               # 操作指南
│   │   ├── deployment.md     # 部署指南
│   │   ├── service-management.md  # 服务管理
│   │   ├── frontend.md       # 前端开发
│   │   ├── project-structure.md   # 本文档
│   │   └── model-management.md    # 模型管理
│   └── architecture/         # 架构文档
│       └── v2-agent-upgrade.md    # V2 Agent 架构
│
├── 📁 uploads/               # 【运行时目录】上传文件
├── 📁 knowledge_base/        # 【运行时目录】RAG 知识库
├── 📁 logs/                  # 【运行时目录】日志文件
│
└── 📁 临时文件（自动生成，不提交）
    ├── __pycache__/          # Python 缓存
    ├── .pytest_cache/        # 测试缓存
    └── node_modules/          # 前端依赖
```

---

## 文件放置规则

### 1. 代码文件

#### 后端代码
```
✅ service/              - 主服务代码
✅ src/agents/          - Agent 系统代码
✅ src/algorithms/      - 算法服务代码
✅ src/rag/             - RAG 系统代码
✅ src/config.py        - 全局配置
```

#### 前端代码
```
✅ frontend/src/        - 所有前端代码
✅ frontend/components/ - React 组件
✅ frontend/app/       - Next.js 页面
```

### 2. 测试文件

```
✅ tests/integration/  - 集成测试
✅ tests/unit/          - 单元测试
❌ src/*/test.py        - 不要在源码目录放测试
```

**命名规范**：
- 测试文件名：`test_<module_name>.py`
- 测试类名：`Test<ClassName>`
- 测试函数名：`test_<function_name>`

### 3. 脚本文件

```
✅ scripts/dev/         - 开发脚本
✅ scripts/deploy/      - 部署脚本
❌ 根目录               - 不要堆在根目录
```

### 4. 文档文件

```
✅ docs/                - 所有项目文档
✅ docs/guides/         - 操作指南
✅ docs/architecture/   - 架构文档
❌ *.md 在根目录         - README.md 除外
```

### 5. 配置文件

```
✅ 根目录               - 项目级配置（.env, pyproject.toml）
✅ service/             - 服务级配置（settings.py）
✅ frontend/            - 前端配置（next.config.mjs）
```

### 6. 数据文件

```
✅ knowledge_base/      - RAG 知识库数据
✅ uploads/             - 用户上传文件
✅ src/algorithms/detection/models/ - AI 模型文件
❌ 数据文件混在代码中   - 避免在 src/ 中混入数据
```

---

## 协作者指南

### 添加新功能时

1. **确定功能类型**
   - Agent 功能 → `src/agents/`
   - 检测功能 → `src/algorithms/detection/`
   - RAG 功能 → `src/rag/`
   - 前端功能 → `frontend/src/`

2. **遵循现有模式**
   - 查看同类功能的实现方式
   - 遵循相同的代码组织结构
   - 使用相同的命名规范

3. **添加测试**
   - 单元测试 → `tests/unit/`
   - 集成测试 → `tests/integration/`

4. **更新文档**
   - API 变更 → 更新 API 文档
   - 架构变更 → 更新架构文档
   - 新功能 → 添加操作指南

### 添加新 Agent 工具时

1. 创建工具文件：`src/agents/tools/<new_tool>.py`
2. 创建对应技能：`src/agents/skills/<new_skill>_skills.py`
3. 在 `orchestrator_agent_v2.py` 中注册工具
4. 添加测试：`tests/unit/test_<new_tool>.py`
5. 更新文档

### 添加新检测服务时

1. 在 `src/algorithms/detection/` 创建服务文件
2. 在 `src/algorithms/api/main.py` 添加路由
3. 添加对应工具：`src/agents/tools/<detection>_tool.py`
4. 更新文档

### 重构代码时

1. **保持目录结构**：不要改变文件所属目录
2. **更新导入**：确保所有导入路径正确
3. **测试覆盖**：确保所有测试通过
4. **文档同步**：同步更新相关文档

---

## 常见问题

### Q1: 测试文件应该放在哪里？

**A**: 所有测试文件统一放在 `tests/` 目录：

```bash
tests/
├── integration/  # 集成测试
└── unit/          # 单元测试
```

不要在源码目录（如 `src/`）中放置测试文件。

### Q2: 脚本文件应该放在哪里？

**A**: 脚本文件统一放在 `scripts/` 目录：

```bash
scripts/
├── dev/      # 开发脚本
└── deploy/   # 部署脚本
```

根目录只保留启动脚本（`run_server.py`, `run_frontend.py`）。

### Q3: 如何组织微服务代码？

**A**:
- **主服务** → `service/`
- **算法服务** → `src/algorithms/`
- **RAG 服务** → `src/rag/service/`

每个服务都有独立的目录和配置。

### Q4: 前端组件如何组织？

**A**: 按功能或类型组织：

```bash
frontend/src/
├── app/              # Next.js 页面
├── components/       # React 组件
│   └── ui/          # 通用 UI 组件
└── utils/           # 工具函数
```

### Q5: 文档应该放在哪里？

**A**: 所有文档放在 `docs/` 目录：

```bash
docs/
├── README.md                    # 文档导航
├── overview/                    # 项目概览
├── guides/                      # 操作指南
└── architecture/                # 架构文档
```

### Q6: 模型文件应该放在哪里？

**A**: AI 模型文件放在对应服务的目录：

```bash
src/algorithms/detection/models/
├── pest/      # 病虫害检测模型
├── rice/      # 大米识别模型
└── cow/       # 奶牛检测模型
```

### Q7: 配置文件应该放在哪里？

**A**:
- **项目级配置** → 根目录（`.env`, `pyproject.toml`）
- **服务级配置** → 服务目录（`service/settings.py`）
- **前端配置** → `frontend/`（`next.config.mjs`）

---

## 代码组织最佳实践

### 1. 模块导入规范

```python
# ✅ 推荐：使用绝对导入
from src.agents.tools import pest_detection_tool
from src.config import ModelManager

# ❌ 避免：相对导入（除非在同一包内）
from ..tools import pest_detection_tool
```

### 2. 命名规范

- **文件名**：小写，下划线分隔（`pest_detection_tool.py`）
- **类名**：大驼峰（`PestDetectionTool`）
- **函数名**：小写，下划线分隔（`detect_pests`）
- **常量**：全大写，下划线分隔（`MAX_IMAGE_SIZE`）

### 3. 文档字符串

```python
def detect_pests(image_path: str) -> dict:
    """
    检测农作物病虫害

    Args:
        image_path: 图片文件路径

    Returns:
        包含检测结果的字典

    Example:
        >>> detect_pests("/path/to/image.jpg")
        {"pests": [{"name": "瓜实蝇", "count": 3}]}
    """
```

### 4. 类型注解

```python
# ✅ 推荐：使用类型注解
def process_detection_result(result: dict) -> str:
    pass

# ✅ 推荐：使用 TypedDict
from typing import TypedDict

class DetectionResult(TypedDict):
    pests: list[dict]
    confidence: float
```

---

## 相关文档

- [部署指南](deployment.md) - Docker 和本地部署
- [服务管理指南](service-management.md) - 服务启动和配置
- [模型管理指南](model-management.md) - 模型配置和切换
- [变更日志](../CHANGELOG.md) - 版本更新记录

---

## 附录：目录职责速查表

| 目录 | 职责 | 示例文件 |
|------|------|----------|
| `service/` | FastAPI 主服务 | `server.py`, `settings.py` |
| `src/agents/` | Agent 系统 | `orchestrator_agent_v2.py` |
| `src/algorithms/` | 算法服务 | `api/main.py`, `detection/` |
| `src/rag/` | RAG 系统 | `service/main.py`, `core/tools.py` |
| `frontend/` | 前端应用 | `src/app/`, `package.json` |
| `tests/` | 测试代码 | `integration/`, `unit/` |
| `scripts/` | 脚本工具 | `dev/`, `deploy/` |
| `docs/` | 项目文档 | `guides/`, `architecture/` |
| `docker/` | Docker 配置 | `docker-compose.yml` |
| `uploads/` | 上传文件 | （运行时生成） |
| `knowledge_base/` | RAG 知识库 | （运行时生成） |

---

**最后更新**: 2026-01-31
**版本**: v2.0

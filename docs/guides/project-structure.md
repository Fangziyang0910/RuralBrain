# RuralBrain 项目结构规范

> **版本**: v3.0
> **更新日期**: 2026-02-11

---

## 核心原则

### 1. 根目录最小化原则

根目录只保留**必须**的配置文件和入口文件。

### 2. 职责分离原则

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

目录层级不超过 3 层（特殊情况除外）。

---

## 文件放置规则

### 代码文件

```
✅ service/              - 主服务代码
✅ src/agents/          - Agent 系统代码
✅ src/algorithms/      - 算法服务代码
✅ src/rag/             - RAG 系统代码
✅ frontend/src/        - 所有前端代码
```

### 测试文件

```
✅ tests/integration/  - 集成测试
✅ tests/unit/          - 单元测试
❌ src/*/test.py        - 不要在源码目录放测试
```

**命名规范**：
- 测试文件名：`test_<module_name>.py`
- 测试类名：`Test<ClassName>`
- 测试函数名：`test_<function_name>`

### 脚本文件

```
✅ scripts/dev/         - 开发脚本
✅ scripts/deploy/      - 部署脚本
❌ 根目录               - 不要堆在根目录（除启动脚本）
```

### 文档文件

```
✅ docs/                - 所有项目文档
✅ docs/architecture/   - 架构设计文档
✅ docs/decisions/      - 重要决策记录
✅ docs/guides/         - 操作指南
❌ *.md 在根目录         - README.md 除外
```

### 配置文件

```
✅ 根目录               - 项目级配置（.env, pyproject.toml）
✅ service/             - 服务级配置（settings.py）
✅ frontend/            - 前端配置（next.config.mjs）
```

---

## 添加新功能时的规范

### 确定功能类型 → 选择目录

| 功能类型 | 目标目录 |
|----------|----------|
| Agent 功能 | `src/agents/` |
| 检测功能 | `src/algorithms/detection/` |
| RAG 功能 | `src/rag/` |
| 前端功能 | `frontend/src/` |

### 添加新 Agent 工具

1. 创建工具文件：`src/agents/tools/<new_tool>.py`
2. 创建对应技能：`src/agents/skills/<new_skill>_skills.py`
3. 在 `orchestrator_agent_v2.py` 中注册工具
4. 添加测试：`tests/unit/test_<new_tool>.py`

### 添加新检测服务

1. 在 `src/algorithms/detection/` 创建服务文件
2. 在 `src/algorithms/api/main.py` 添加路由
3. 添加对应工具：`src/agents/tools/<detection>_tool.py`

---

## 常见问题

### Q: 测试文件应该放在哪里？

所有测试文件统一放在 `tests/` 目录，不要在源码目录（如 `src/`）中放置测试文件。

### Q: 脚本文件应该放在哪里？

脚本文件统一放在 `scripts/` 目录。根目录只保留启动脚本（`run_server.py`, `run_frontend.py`）。

### Q: 文档应该放在哪里？

所有文档放在 `docs/` 目录：
- `docs/architecture/` - 架构设计文档（设计思想）
- `docs/decisions/` - 重要决策记录
- `docs/guides/` - 操作指南

### Q: 模型文件应该放在哪里？

AI 模型文件放在对应服务的目录：
```bash
src/algorithms/detection/models/
├── pest/      # 病虫害检测模型
├── rice/      # 大米识别模型
└── cow/       # 奶牛检测模型
```

---

## 相关文档

- [系统架构设计](../architecture/system-design.md) - 整体架构设计理念
- [微服务架构设计](../architecture/microservices.md) - 微服务拆分说明

---

**最后更新**: 2026-02-11
**版本**: v3.0

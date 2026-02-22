# Skills 开发指南

本文档说明如何为 RuralBrain 添加新技能。

---

## 快速概览

| 场景 | 需要创建/修改的文件 |
|------|---------------------|
| **仅使用现有工具** | YAML + `<capabilities>` + `<examples>` |
| **需要新工具** | 工具 + YAML + 系统提示词 + 工具注册 |
| **需要外部服务** | 以上 + 服务配置 |

---

## 添加新技能的步骤

### 步骤 1：创建 YAML 配置

**位置**：`src/agents/skills/configs/<category>.yaml`

```yaml
skill_name:
  description: 简短描述（20字以内）
  tool_names:
    - existing_tool_1    # 可选
  content: |
    技能完整内容...
```

### 步骤 2：更新系统提示词

**文件**：`src/agents/orchestrator_agent_v2.py`

需要修改 2 个地方：

| 位置 | 内容 |
|------|------|
| `<capabilities>` | 添加能力类别：`**新类别**: 描述...` |
| `<examples>` | 添加使用示例（建议） |

**不需要修改**：
- `<workflow>` - 技能列表由中间件自动注入
- 映射关系 - Agent 根据技能描述自动判断

### 步骤 3：如果有新工具

```
✓ 新建：src/agents/tools/<tool_name>_tool.py
✓ 修改：src/agents/tools/__init__.py          # 导出工具
✓ 修改：src/agents/orchestrator_agent_v2.py   # 注册工具到列表
```

### 步骤 4：测试验证

```bash
bash scripts/dev/check.sh --quick
```

---

## 系统提示词结构

```
<role>
角色定义
</role>

<capabilities>
**检测**: ...
**新类别**: 新技能描述...        ← 添加这里
</capabilities>

<workflow>
通用工作流程（不需要维护技能映射）
</workflow>

<examples>
**新技能示例**:                      ← 添加示例（建议）
1. load_skill("skill_name")
...
</examples>
```

---

## 技能加载机制

```
服务启动
    ↓
SkillRegistry 扫描 configs/ 目录
    ↓
自动加载所有 YAML 配置
    ↓
SkillMiddleware 动态注入技能描述
    ↓
Agent 看到完整技能列表
```

**关键点**：
- 添加 YAML 后技能自动加载
- 技能描述自动注入到系统提示词
- Agent 根据技能描述自动判断何时调用

---

## YAML 配置规范

### 文件命名

| 类别 | 文件名 |
|------|--------|
| 检测类 | `detection.yaml` |
| 规划类 | `planning.yaml` |
| 分析类 | `<domain>.yaml` |

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `description` | ✓ | 简短描述（自动注入系统提示词） |
| `tool_names` | - | 关联的工具列表 |
| `content` | ✓ | 完整技能内容（按需加载） |

---

## 相关文档

- [V2 Agent 架构设计](../architecture/v2-agent-architecture.md) - Skills 架构原理
- [开发工作流](development.md) - 热重载和测试流程

---

**最后更新**: 2026-02-20

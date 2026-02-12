# Agent V2 迁移决策

## 决策背景

### V1 架构的问题

原始的 Orchestrator Agent V1 采用传统的**固定提示词**架构：

```python
# V1 系统提示词（固定加载所有内容）
system_prompt = """
你是 RuralBrain 的智能助手...

## 工具列表（9个工具，全部在提示词中描述）
1. pest_detection_tool - 病虫害检测
2. rice_detection_tool - 大米品种识别
...
（82行提示词）
"""
```

### 存在的问题

1. **Token 消耗高**
   - 系统提示词固定包含所有工具描述
   - 无论使用与否，每次请求都消耗 ~2000 tokens
   - 成本高，响应慢

2. **扩展困难**
   - 新增工具需要修改核心提示词
   - 提示词越来越长，难以维护
   - 工具描述与定义分散

3. **灵活性不足**
   - 无法根据场景动态加载能力
   - 所有工具始终"在线"
   - 无法渐进式披露能力

---

## 决策方案：Skills 架构

### 设计理念：Progressive Disclosure（渐进式披露）

基于 LangChain 官方的 [Skills 模式](https://python.langchain.com/docs/modules/agents/agent_types/custom_conceptual_agent/#skills-pattern)：

- **初始状态**：只提供技能的简短描述
- **按需加载**：Agent 需要时通过 `load_skill` 工具获取详细指导
- **Token 优化**：详细内容只在需要时加载

### V2 架构设计

```
Orchestrator Agent V2
    │
    ├─ Skills 架构
    │   ├─ pest_detection（病虫害检测技能）
    │   ├─ rice_detection（大米识别技能）
    │   ├─ cow_detection（奶牛检测技能）
    │   ├─ consult_planning_knowledge（规划咨询技能）
    │   ├─ intent_recognition（意图识别技能）
    │   └─ scenario_switching（场景切换技能）
    │
    ├─ 中间件系统
    │   ├─ SkillMiddleware（按需加载技能）
    │   └─ ToolSelectorMiddleware（工具选择）
    │
    └─ 工具系统（9个工具）
```

### 核心实现

**1. Skill 定义**

```python
# src/agents/skills/detection_skills.py
def create_pest_detection_skill() -> Skill:
    return Skill(
        name="pest_detection",
        description="病虫害检测专家",
        system_prompt="""详细的病虫害检测指导...""",
        tools=[pest_detection_tool],
        examples=[...],
        constraints=[...],
    )
```

**2. load_skill 工具**

```python
def load_skill(skill_name: str) -> str:
    """按需加载技能的详细指导"""
    skill = skills.get(skill_name)
    if skill:
        return f"## {skill.name}\n\n{skill.system_prompt}"
    return f"技能 {skill_name} 不存在"
```

**3. 简化的系统提示词**

```python
# V2 系统提示词（仅 20 行）
system_prompt = """
你是 RuralBrain 的智能助手。

## 可用技能
- pest_detection：病虫害检测
- rice_detection：大米品种识别
- consult_planning_knowledge：规划咨询

## 工作流程
1. 理解用户意图
2. 需要详细了解时，使用 load_skill 工具
3. 选择合适的工具完成任务
"""
```

---

## 方案对比

| 方面 | V1（固定提示词） | V2（Skills 架构） |
|------|------------------|-------------------|
| **系统提示词** | 82 行 | 20 行 (-76%) |
| **Token 消耗** | ~2000 tokens/请求 | ~1000 tokens/请求 (-50%) |
| **扩展性** | 修改核心提示词 | 新增 Skill 文件 |
| **灵活性** | 固定加载所有能力 | 按需加载 |
| **维护性** | 提示词臃肿 | 模块化清晰 |

---

## 实施过程

### 第一阶段：架构设计

1. 研究 LangChain Skills 模式
2. 设计 Skill 数据结构
3. 设计中间件系统

### 第二阶段：核心实现

1. 实现 `SkillMiddleware`（按需加载）
2. 实现 `ToolSelectorMiddleware`（工具选择）
3. 创建各技能定义文件

### 第三阶段：迁移适配

1. 保留 V1 作为后备（`AGENT_VERSION=v1`）
2. 实现 V2 Agent
3. 添加自动降级机制

### 第四阶段：测试验证

1. 功能测试：所有场景正常工作
2. 性能测试：Token 消耗对比
3. 降级测试：V2 失败时自动切换到 V1

---

## 效果评估

### 定量改进

| 指标 | V1 | V2 | 改进 |
|------|----|----|----|
| 系统提示词行数 | 82 | 20 | -76% |
| Token 消耗/请求 | ~2000 | ~1000 | -50% |
| 新增技能成本 | 修改核心文件 | 新增文件 | 低 |
| 响应延迟 | 基准 | +<10% | 可接受 |

### 定性改进

1. **开发效率**
   - 新增技能无需修改核心文件
   - 模块化清晰，易于维护

2. **系统稳定性**
   - 支持 V1/V2 版本切换
   - 自动降级机制

3. **扩展性**
   - 技能独立开发和测试
   - 支持技能版本管理

---

## 配置方式

### 环境变量

```bash
# .env
AGENT_VERSION=v2              # 使用 V2
AGENT_AUTO_FALLBACK=true      # V2 失败时自动切换到 V1
```

### 切换版本

```bash
# 切换到 V1
AGENT_VERSION=v1

# 切换到 V2
AGENT_VERSION=v2
```

---

## 权衡和代价

### 优点

1. Token 消耗降低 50%+
2. 系统提示词更简洁
3. 模块化易于扩展
4. 支持版本切换和自动降级

### 缺点

1. **响应延迟增加**：`load_skill` 需要额外调用
   - 评估：延迟增加 <10%，用户无感知

2. **复杂度增加**：引入了中间件和 Skill 系统
   - 缓解：清晰的架构设计，完善的文档

3. **学习成本**：新开发者需要理解 Skills 模式
   - 缓解：详细的架构文档和示例

---

## 后续优化方向

### 短期

1. 优化 `load_skill` 调用时机
2. 添加技能缓存机制
3. 完善技能版本管理

### 长期

1. 支持技能的动态加载（从文件或数据库）
2. 技能 marketplace（第三方技能扩展）
3. 技能性能分析和优化

---

## 相关文档

- [V2 Agent 架构设计](../architecture/v2-agent-architecture.md)
- [系统架构设计](../architecture/system-design.md)
- [统一命令参考](../commands.md)

---

**决策日期**: 2026-01-20
**决策状态**: 已实施并稳定运行
**效果**: Token 消耗降低 50%+，维护成本显著降低

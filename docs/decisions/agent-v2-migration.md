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

**1. Skill 定义（YAML 配置）**

```yaml
# src/agents/skills/configs/detection.yaml
pest_detection:
  description: 病虫害检测专家，识别农作物病虫害并提供防治建议
  tool_names:
    - pest_detection_tool
  content: |
    你是病虫害检测专家，专注于农作物的病虫害识别和防治。

    ## 核心能力
    - 识别常见农作物病虫害（瓜实蝇、斜纹夜蛾、稻飞虱等）
    - 分析病虫害危害程度和传播风险
    - 提供科学的预防措施建议和针对性的综合防治方案

    ## 工作流程
    1. 使用 `pest_detection_tool` 分析图片
    2. 根据检测结果识别害虫种类和数量
    3. 评估危害程度和对作物的影响
    4. 提供多层次防治方案（化学、生物、物理防治）
    5. 给出预防措施和农事管理建议
```

**2. Skill 数据模型（简化版）**

```python
# src/agents/skills/base.py
class Skill(BaseModel):
    """技能数据类 - 基于 LangChain Skills 模式"""
    name: str                    # 技能唯一标识
    description: str             # 简短描述（1-2 句话）
    content: str                 # 完整内容（按需加载）
    tool_names: List[str]        # 关联的工具名称列表
    references: List[str]        # 参考资源列表
```

**2. load_skill 工具**

```python
def load_skill(skill_name: str) -> str:
    """按需加载技能的详细指导"""
    skill = skills.get(skill_name)
    if skill:
        return f"## {skill.name}\n\n{skill.content}"
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
2. 设计 Skill 数据结构（Pydantic BaseModel）
3. 设计中间件系统

### 第二阶段：核心实现

1. 实现 `SkillMiddleware`（按需加载）
2. 实现 `ToolSelectorMiddleware`（工具选择）
3. 创建各技能定义文件（Python 代码）

### 第三阶段：配置迁移

1. 创建技能注册中心（`registry.py`）
2. 将技能定义从 Python 迁移到 YAML 配置
3. 支持技能热重载

### 第四阶段：测试验证

1. 功能测试：所有场景正常工作
2. 性能测试：Token 消耗对比
3. 配置验证：YAML 配置正确加载

---

## 效果评估

### 定量改进

| 指标 | V1 | V2 | 改进 |
|------|----|----|----|
| 系统提示词行数 | 82 | 20 | -76% |
| Token 消耗/请求 | ~2000 | ~1000 | -50% |
| 新增技能成本 | 修改核心文件 | 新增 YAML 文件 | 显著降低 |
| 技能维护 | 分散在代码中 | 集中在配置文件 | 易维护 |

### 定性改进

1. **开发效率**
   - 新增技能仅需添加 YAML 配置
   - 技能注册中心统一管理
   - 支持热重载，无需重启服务

2. **代码质量**
   - Skill 数据模型使用 Pydantic，自动验证
   - 配置与代码分离，职责清晰
   - 移除冗余代码（-1000+ 行）

3. **扩展性**
   - 技能独立配置和测试
   - 支持动态工具注册
   - 支持技能参考资源

---

## 配置方式

### 环境变量

```bash
# .env
# 技能重新加载策略: always（每次）| timed（定时）| never（从不）
SKILL_RELOAD_STRATEGY=always
SKILL_RELOAD_INTERVAL=300      # 重新加载间隔（秒）
```

### 技能重新加载策略

- **always**: 每次请求都重新加载技能配置（适合开发环境）
- **timed**: 按时间间隔重新加载（适合生产环境）
- **never**: 从不自动重新加载（适合高性能环境）

---

## 权衡和代价

### 优点

1. Token 消耗降低 50%+
2. 系统提示词更简洁
3. YAML 配置易于维护和扩展
4. 技能注册中心统一管理
5. 支持智能重新加载策略

### 缺点

1. **响应延迟增加**：`load_skill` 需要额外调用
   - 评估：延迟增加 <10%，用户无感知

2. **复杂度增加**：引入了中间件和注册中心系统
   - 缓解：清晰的架构设计，完善的文档

3. **学习成本**：新开发者需要理解 Skills 模式
   - 缓解：详细的架构文档和示例

---

## 后续优化方向

### 短期

1. ✅ 技能配置从 Python 迁移到 YAML
2. ✅ 技能注册中心统一管理
3. ✅ 支持智能重新加载策略

### 长期

1. 支持技能的动态版本管理
2. 技能性能分析和优化
3. 技能依赖管理（技能间的依赖关系）

---

## 相关文档

- [V2 Agent 架构设计](../architecture/v2-agent-architecture.md)
- [系统架构设计](../architecture/system-design.md)
- [统一命令参考](../commands.md)

---

**决策日期**: 2026-01-20
**最后更新**: 2026-02-20
**决策状态**: 已实施并稳定运行
**效果**: Token 消耗降低 50%+，维护成本显著降低，YAML 配置驱动

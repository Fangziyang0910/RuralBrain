# RuralBrain Agent 架构升级方案

## 一、设计概述

基于 LangChain 官方 **Skills 模式**和 **Progressive Disclosure（渐进式披露）**最佳实践，将 RuralBrain 从固定提示词+硬编码工具的架构，升级为模块化、可扩展的 Agent Skills 架构。

### 核心目标

| 维度 | 改造前 | 改造后 | 提升 |
|------|--------|--------|------|
| **提示词长度** | 82-124 行 | 10-20 行 | 减少 75%+ |
| **Token 消耗** | 所有技能始终加载 | 按需加载 | 减少 50%+ |
| **扩展性** | 硬编码，需修改代码 | YAML 配置 | 质的飞跃 |
| **维护成本** | 提示词分散在各文件 | 模块化技能配置 | 降低 60%+ |

### 核心设计理念

1. **Progressive Disclosure（渐进式披露）**：初始只提供技能描述，需要时再加载完整内容
2. **Single Responsibility（单一职责）**：每个技能专注于一个特定领域
3. **Configuration over Code（配置优于代码）**：技能定义使用 YAML 配置文件
4. **Composability（可组合性）**：技能可组合、可复用

---

## 二、架构设计

### 2.1 技能抽象层（Skill Abstraction）

**核心概念**：将专门的能力（如病虫害检测、大米识别、乡村规划）打包成独立的 Skill。

```python
# src/agents/skills/base.py
@dataclass
class Skill:
    name: str                        # 技能唯一标识
    description: str                 # 简短描述（显示在系统提示词中）
    category: str                    # 分类：detection/planning/analysis
    system_prompt: Optional[str]     # 完整系统提示词（按需加载）
    tools: List[BaseTool]            # 技能专属工具
    examples: List[str]              # Few-shot 示例
    constraints: List[str]           # 约束条件
```

**技能配置文件示例**：

```yaml
# src/agents/skills/configs/pest_detection.yaml
name: pest_detection
description: 病虫害检测专家，识别农作物病虫害并提供防治建议
category: detection

system_prompt: |
  你是病虫害检测专家，专注于农作物的病虫害识别和防治。

  ## 核心能力
  - 识别常见农作物病虫害（如瓜实蝇、斜纹夜蛾等）
  - 分析病虫害危害程度
  - 提供针对性的防治方案（化学、生物、物理防治）
  - 给出预防建议

tools:
  - pest_detection_tool

examples:
  - "用户上传图片并问'这是什么害虫？' → 调用检测工具 → 识别为瓜实蝇 → 提供防治方案"

constraints:
  - 必须基于检测结果提供建议，不得虚构
  - 防治方案应包括化学、生物、物理多种方式
```

### 2.2 中间件架构（Middleware）

#### SkillMiddleware - 技能中间件

**功能**：
- 将技能描述注入到系统提示词中
- 注册 `load_skill` 工具
- 实现渐进式披露

```python
class SkillMiddleware(AgentMiddleware):
    """技能中间件 - 实现 Progressive Disclosure"""

    tools = [load_skill]  # 注册 load_skill 工具

    def wrap_model_call(self, request, handler):
        # 将技能描述列表注入系统提示词
        skills_addendum = "## Available Skills\n\n- pest_detection: 病虫害检测专家\n- rice_detection: 大米识别专家"
        modified_request = request.override(system_message=...)
        return handler(modified_request)
```

#### ToolSelectorMiddleware - 工具选择中间件

**功能**：
- 根据上下文动态选择工具子集
- 减少工具列表长度，提高 Agent 决策准确性

```python
class ToolSelectorMiddleware(AgentMiddleware):
    """工具选择中间件 - 动态选择相关工具"""

    def wrap_model_call(self, request, handler):
        # 根据标签选择相关工具
        relevant_tools = registry.get_by_tags(["detection"])
        modified_request = request.override(tools=relevant_tools)
        return handler(modified_request)
```

### 2.3 智能路由系统（LangGraph StateGraph）

**基于 LangGraph 的动态工作流**：

```python
# 路由流程
START → classify_intent → route_decision → [detection/planning/general]_agent → END

# classify_intent: 识别用户意图
# route_decision: 决定路由到哪个 Agent
# [agent]_node: 执行具体的 Agent 逻辑
```

**意图识别规则**：
- 有图片 + 检测关键词 → `detection_agent`
- 规划相关关键词 → `planning_agent`
- 其他 → `general_agent`

---

## 三、实施路径（聚焦 Phase 3 中间件）

### 实施策略：渐进式迁移

**原则**：
- 新旧代码共存，不影响现有功能
- 新增基于 Skills 的 Agent 作为平行实现
- 充分验证后再逐步替换旧代码

### 第一阶段：核心中间件实现（优先）

**目标**：实现 SkillMiddleware 和 Progressive Disclosure 核心机制

**任务清单**：
- [ ] 创建 `src/agents/middleware/` 目录
- [ ] 实现 `load_skill` 工具（按需加载技能内容）
- [ ] 实现 `SkillMiddleware`（技能描述注入 + 渐进式披露）
- [ ] 实现 `ToolSelectorMiddleware`（动态工具选择）
- [ ] 创建简化的 Skill 数据结构（先用 Python dataclass，后续迁移到 YAML）
- [ ] 编写第一个技能示例：病虫害检测技能
- [ ] 创建新的 `image_detection_agent_v2.py`（基于 Skills 架构）
- [ ] 并行测试：对比新旧 Agent 的输出质量

**关键文件**：
- `src/agents/middleware/__init__.py`
- `src/agents/middleware/skill_middleware.py`（核心）
- `src/agents/middleware/tool_selector_middleware.py`
- `src/agents/skills/base.py`（简化版 Skill 类）
- `src/agents/image_detection_agent_v2.py`（新版本）

**验证标准**：
- `load_skill` 工具能正确返回技能完整内容
- Agent 能自主判断何时调用 `load_skill`
- 新 Agent 输出质量不低于旧版本

### 第二阶段：技能配置化（YAML）

**目标**：将技能定义迁移到 YAML 配置文件

**任务清单**：
- [ ] 创建 `src/agents/skills/configs/` 目录
- [ ] 设计 YAML 配置文件格式
- [ ] 编写技能配置文件：
  - [ ] `pest_detection.yaml`
  - [ ] `rice_detection.yaml`
  - [ ] `cow_detection.yaml`
  - [ ] `rural_planning.yaml`
- [ ] 实现 `SkillLoader`（从 YAML 加载技能）
- [ ] 实现 `SkillRegistry`（技能注册和管理）
- [ ] 更新 `image_detection_agent_v2.py` 使用 YAML 配置

**关键文件**：
- `src/agents/skills/configs/pest_detection.yaml`
- `src/agents/skills/configs/rice_detection.yaml`
- `src/agents/skills/configs/cow_detection.yaml`
- `src/agents/skills/registry.py`
- `src/agents/skills/loader.py`

### 第三阶段：完善和验证

**目标**：完善功能，全面测试

**任务清单**：
- [ ] 实现 `planning_agent_v2.py`（基于 Skills）
- [ ] 添加技能标签系统（category, tags）
- [ ] 实现中间件链（`MiddlewareChain`）
- [ ] 添加日志和监控（LangSmith 集成）
- [ ] 性能测试：Token 消耗、响应延迟
- [ ] 输出质量对比测试
- [ ] 编写迁移文档

### 第四阶段（可选）：智能路由

**目标**：基于 LangGraph 实现智能路由

**任务清单**：
- [ ] 定义 Agent 状态（`router/state.py`）
- [ ] 实现意图识别节点
- [ ] 创建 StateGraph 工作流
- [ ] 集成到服务端

### 第五阶段（可选）：完整迁移

**目标**：完全替换旧代码

**任务清单**：
- [ ] 验证新版本稳定性
- [ ] 重命名 `v2` 文件替换旧版本
- [ ] 更新服务端引用
- [ ] 清理旧代码

---

## 四、代码对比示例

### 改造前：固定提示词（82 行）

```python
# src/agents/image_detection_agent.py (当前实现)
SYSTEM_PROMPT = """
<role>
你是一位多模态农业专家助手...
</role>

<tools>
你可以调用以下三个图像识别工具：
1. pest_detection_tool - 功能描述...
2. rice_detection_tool - 功能描述...
3. cow_detection_tool - 功能描述...
</tools>

<task>
你的完整工作流程如下：
1. 判断用户意图
2. 工具调用策略
3. 解释与分析结果
4. 提供专家级建议
5. 多轮对话支持
</task>

<constraints>
- 回答必须基于工具结果，不得虚构检测内容
- 工具返回失败时，要礼貌地说明问题并建议用户重试
- 保持自然、专业、友好的语气
- 不要使用过度格式化
</constraints>

<output_format>
- 回复清晰、自然、有逻辑
- 必要时分点说明关键内容
- 对每类识别任务都包含实际可操作的建议
</output_format>

<demo_mode>
- 现在处于演示模式，回答200字左右，不能超过300字
- 回答应简洁明了，突出重点
</demo_mode>
"""

agent = create_agent(
    model=model,
    tools=[pest_detection_tool, rice_detection_tool, cow_detection_tool],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=InMemorySaver(),
)
```

### 改造后：基于 Skills（20 行）

```python
# src/agents/image_detection_agent.py (新实现)
from langchain.agents import create_agent
from ..skills.registry import SkillRegistry
from ..middleware.skill_middleware import SkillMiddleware
from ..middleware.tool_selector_middleware import ToolSelectorMiddleware

# 基础提示词（大幅简化）
BASE_SYSTEM_PROMPT = """
<role>
你是一位多模态农业专家助手，能够根据用户的需求在多种图像识别任务之间进行智能选择。
</role>

<task>
根据用户的输入自动判断需要使用哪个工具，并在必要时调用工具进行分析。
</task>

<constraints>
- 回答必须基于工具结果，不得虚构检测内容
- 保持自然、专业、友好的语气
</constraints>
"""

# 加载检测相关技能
skill_registry = SkillRegistry()
detection_skills = skill_registry.list_by_category("detection")

# 创建中间件
skill_middleware = SkillMiddleware(skills=detection_skills)
tool_selector = ToolSelectorMiddleware(tags=["detection"])

# 创建 Agent（使用 Skills 架构）
agent = create_agent(
    model=model,
    tools=[],  # 工具由中间件动态注入
    system_prompt=BASE_SYSTEM_PROMPT,
    middleware=[skill_middleware, tool_selector],
    checkpointer=InMemorySaver(),
)
```

---

## 五、新增目录结构

```
src/agents/
├── skills/                      # 技能系统（新增）
│   ├── __init__.py
│   ├── base.py                 # Skill 基类
│   ├── registry.py             # 技能注册中心
│   ├── configs/                # 技能配置文件
│   │   ├── pest_detection.yaml
│   │   ├── rice_detection.yaml
│   │   ├── cow_detection.yaml
│   │   └── rural_planning.yaml
│   └── loader.py               # 技能加载器
│
├── tools/                       # 工具系统（重构）
│   ├── __init__.py
│   ├── registry.py             # 工具注册中心（新增）
│   ├── configs/                # 工具配置文件（新增）
│   │   ├── detection_tools.yaml
│   │   └── planning_tools.yaml
│   ├── pest_detection_tool.py  # 现有工具（保持不变）
│   ├── rice_detection_tool.py
│   └── cow_detection_tool.py
│
├── prompts/                     # 提示词系统（新增）
│   ├── __init__.py
│   ├── templates.py            # 提示词模板
│   ├── builder.py              # 动态构建器
│   └── components.py           # 公共组件库
│
├── middleware/                  # 中间件系统（新增）
│   ├── __init__.py
│   ├── skill_middleware.py     # 技能中间件
│   ├── tool_selector_middleware.py  # 工具选择中间件
│   └── chain.py                # 中间件链
│
├── router/                      # 路由系统（新增）
│   ├── __init__.py
│   ├── state.py                # 状态定义
│   ├── intent_classifier.py    # 意图识别
│   ├── router.py               # 路由决策
│   └── graph.py                # StateGraph 工作流
│
├── image_detection_agent.py     # 重构后的图像检测 Agent
├── planning_agent.py            # 重构后的规划咨询 Agent
└── general_agent.py             # 新增：通用对话 Agent
```

---

## 六、验证和测试

### 功能测试

- [ ] 技能可以从 YAML 文件正确加载
- [ ] `load_skill` 工具能按需加载技能内容
- [ ] 中间件能正确注入技能描述
- [ ] 工具选择中间件能根据标签动态选择工具
- [ ] 意图识别准确率 > 90%
- [ ] 路由决策正确
- [ ] 输出质量不下降（与改造前对比）

### 性能测试

- [ ] Token 消耗减少 50%+
- [ ] 响应延迟增加 < 10%
- [ ] 技能加载时间 < 100ms

### 兼容性测试

- [ ] 现有 API 接口保持兼容
- [ ] 现有功能不受影响
- [ ] LangSmith 追踪正常工作

---

## 七、关键文件清单

实施此架构升级方案最关键的 5 个文件：

1. **`src/agents/skills/base.py`** - Skill 基类定义
2. **`src/agents/skills/registry.py`** - 技能注册中心
3. **`src/agents/middleware/skill_middleware.py`** - 技能中间件（实现渐进式披露）
4. **`src/agents/router/graph.py`** - StateGraph 工作流（智能路由）
5. **`src/agents/tools/registry.py`** - 工具注册中心

---

## 八、参考资料

- [LangChain Skills 官方文档](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)
- [Build a SQL assistant with on-demand skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills-sql-assistant)
- [AgentMiddleware 实现文档](https://docs.langchain.com/oss/python/langchain/middleware/custom)
- [LangGraph StateGraph 文档](https://langchain-ai.github.io/langgraph/)

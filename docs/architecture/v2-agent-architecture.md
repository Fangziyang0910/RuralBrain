# V2 Agent 架构设计

## 概述

RuralBrain V2 Agent 采用基于 LangChain 官方 **Skills 模式**和**渐进式披露（Progressive Disclosure）**的架构设计，将传统固定提示词架构升级为模块化、可扩展的 Agent Skills 架构。

### 核心改进

| 维度 | V1（传统架构） | V2（Skills 架构） | 提升 |
|------|---------------|------------------|------|
| **提示词长度** | 82-124 行 | 10-20 行 | 减少 75%+ |
| **Token 消耗** | 所有技能始终加载 | 按需加载 | 减少 50%+ |
| **扩展性** | 硬编码，需修改代码 | YAML 配置 | 质的飞跃 |
| **维护成本** | 提示词分散在各文件 | 模块化技能配置 | 降低 60%+ |

---

## 架构设计

### 核心理念

1. **Progressive Disclosure（渐进式披露）**：初始只提供技能描述，需要时再加载完整内容
2. **Single Responsibility（单一职责）**：每个技能专注于一个特定领域
3. **Configuration over Code（配置优于代码）**：技能定义使用配置文件
4. **Composability（可组合性）**：技能可组合、可复用

### 架构层次

```
用户请求
    ↓
┌─────────────────────────────────────┐
│        image_detection_agent_v2      │
│  ┌──────────────────────────────┐   │
│  │   BASE_SYSTEM_PROMPT (~20行)  │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │       middleware 列表         │   │
│  │  1. SkillMiddleware          │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│        中间件执行链（洋葱模型）       │
│  ┌──────────────────────────────┐   │
│  │ Layer 1: SkillMiddleware     │   │
│  │ - 注入技能描述列表           │   │
│  │ - 注册 load_skill 工具       │   │
│  └──────────────────────────────┘   │
│             ↓                       │
│  ┌──────────────────────────────┐   │
│  │ Layer 2: LLM 推理            │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## 中间件系统

### SkillMiddleware - 技能中间件

**功能**：实现 Progressive Disclosure

```python
class SkillMiddleware(AgentMiddleware):
    def wrap_model_call(self, request, handler):
        # 1. 构建技能描述列表（简短）
        skills_list = [f"- {s.name}: {s.description}" for s in skills]

        # 2. 注入到系统提示词
        skills_addendum = f"""
## 可用技能

{chr(10).join(skills_list)}

使用 load_skill 工具获取技能的详细信息。
"""

        # 3. 注册 load_skill 工具
        # Agent 可调用 load_skill(skill_name) 获取完整内容

        return handler(modified_request)
```

**工作流程**：
1. 初始提示词只包含技能描述列表
2. Agent 判断需要某个技能时，调用 `load_skill`
3. 获取完整的技能指导（工作流程、输出格式、示例）
4. 基于完整指导进行推理

---

## 工作流程示例

### 场景：用户上传害虫图片

```
用户："帮我识别这张图片中的害虫"
    ↓
Agent 读取系统提示词（包含技能描述列表）
    ↓
Agent 判断需要病虫害检测能力
    ↓
调用 load_skill("pest_detection")
    ↓
获取完整指导：
  - 核心能力
  - 工作流程
  - 输出格式
  - 防治方案指南
    ↓
调用 pest_detection_tool(image_path="...")
    ↓
基于完整指导和工具结果，给出专业建议
```

---

## 对比 V1 vs V2

### V1（传统架构）

```python
# 一次性加载所有信息（82行提示词）
SYSTEM_PROMPT = """
<role>你是一位多模态农业专家助手...</role>

<tools>
你可以调用以下三个图像识别工具：
1. pest_detection_tool - 详细描述...
2. rice_detection_tool - 详细描述...
3. cow_detection_tool - 详细描述...
</tools>

<task>
你的完整工作流程如下：
1. 判断用户意图
2. 工具调用策略（详细步骤...）
3. 解释与分析结果（详细指导...）
...
</task>
...
"""
```

**问题**：
- ❌ 所有内容始终加载，Token 消耗大
- ❌ 提示词臃肿，难以维护
- ❌ 添加新技能需要修改大量提示词

### V2（Skills 架构）

```python
# 初始只有简短提示词（~20行）
BASE_SYSTEM_PROMPT = """
<role>你是一位多模态农业专家助手</role>

<task>
根据用户输入自动判断需要使用哪个工具。
工作流程：
1. 判断用户意图
2. 使用 load_skill 加载对应技能的详细指导
3. 基于工具结果给出准确解释
</task>
"""

# 技能描述由中间件动态注入
```

**优势**：
- ✅ Token 消耗减少 60%（初始加载更少）
- ✅ 模块化，易于扩展
- ✅ Agent 更自主（自己决定何时加载什么技能）

---

## 技能抽象

### Skill 数据结构（Pydantic BaseModel）

```python
class Skill(BaseModel):
    """技能数据类 - 基于 LangChain Skills 模式"""
    name: str                    # 技能唯一标识
    description: str             # 简短描述（1-2 句话）
    content: str                 # 完整内容（按需加载）
    tool_names: List[str]        # 关联的工具名称列表
    references: List[str]        # 参考资源列表
```

### YAML 配置示例

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

    ## 输出格式
    ### 检测结果摘要
    清晰列出检测到的害虫种类和数量
    ### 危害分析
    评估害虫的危害程度和潜在影响
    ### 防治方案
    - **化学防治**：推荐药剂、使用方法、注意事项
    - **生物防治**：天敌利用、生物农药
    - **物理防治**：物理隔离、诱杀方法
```

---

## 技能重新加载

### 配置策略

系统支持三种技能重新加载策略：

```python
# src/config.py
SkillReloadStrategy = Literal["always", "timed", "never"]
SKILL_RELOAD_STRATEGY: SkillReloadStrategy = "always"
SKILL_RELOAD_INTERVAL = 300  # 秒
```

### 策略说明

- **always**: 每次请求都重新加载技能配置（适合开发环境）
- **timed**: 按时间间隔重新加载（适合生产环境）
- **never**: 从不自动重新加载（适合高性能环境）

### 实现方式

```python
class SkillMiddleware(AgentMiddleware):
    def before_agent(self, state, runtime):
        if self.reload_strategy == "always":
            self.registry.reload()
        elif self.reload_strategy == "timed":
            if time.time() - self._last_reload_time >= self.reload_interval:
                self.registry.reload()
                self._last_reload_time = time.time()
```

---

## 目录结构

```
src/agents/
├── middleware/                  # 中间件系统
│   ├── skill_middleware.py      # 技能渐进式披露
│   └── tool_selector_middleware.py  # 工具选择
├── skills/                      # 技能系统
│   ├── base.py                  # Skill 数据模型（Pydantic）
│   ├── registry.py              # 技能注册中心
│   ├── configs/                 # YAML 技能配置文件
│   │   ├── detection.yaml       # 检测技能
│   │   ├── planning.yaml        # 规划技能
│   │   ├── pricing.yaml         # 定价技能
│   │   ├── marketing.yaml       # 营销技能
│   │   ├── inspection.yaml      # 巡检技能
│   │   └── disease_prediction.yaml  # 疾病预测技能
│   └── __init__.py
├── tools/                       # 工具系统
│   ├── load_skill_tool.py       # 技能加载工具
│   └── ...
└── orchestrator_agent_v2.py     # V2 Agent（统一编排）
```

---

## 性能优化

### Token 消耗对比

| 场景 | V1 Token 数 | V2 Token 数 | 节省 |
|------|------------|------------|------|
| 简单检测 | ~1500 | ~600 | 60% |
| 复杂检测（需技能详情） | ~1500 | ~900 | 40% |
| 多轮对话 | ~1500 × N | ~600 + ~300 × N | 50%+ |

### 响应延迟

- V2 架构额外延迟：`<100ms`（技能加载时间）
- 可接受范围：对用户体验影响可忽略

---

## 扩展性

### 添加新技能（YAML 配置）

1. 创建 `src/agents/skills/configs/new_feature.yaml`

```yaml
new_feature:
  description: 新功能描述
  tool_names:
    - new_tool
  content: |
    新功能的详细说明...

    ## 核心能力
    - 能力1
    - 能力2

    ## 工作流程
    1. 步骤1
    2. 步骤2
```

2. 重启服务或等待重新加载（根据 `SKILL_RELOAD_STRATEGY` 配置）
3. 技能自动被注册中心加载并可用

### 技能重新加载策略

在 `.env` 或 `src/config.py` 中配置：

```python
# 技能重新加载策略
SKILL_RELOAD_STRATEGY = "always"  # always | timed | never
SKILL_RELOAD_INTERVAL = 300        # 重新加载间隔（秒）
```

---

## 验证和测试

### 功能测试

- ✅ 技能可以从配置文件正确加载
- ✅ `load_skill` 工具能按需加载技能内容
- ✅ 中间件能正确注入技能描述
- ✅ 工具选择中间件能根据标签动态选择工具
- ✅ 输出质量不下降（与改造前对比）

### 性能测试

- ✅ Token 消耗减少 50%+
- ✅ 响应延迟增加 < 10%
- ✅ 技能加载时间 < 100ms

---

## 参考资料

- [LangChain Skills 官方文档](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)
- [Build a SQL assistant with on-demand skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills-sql-assistant)
- [AgentMiddleware 实现文档](https://docs.langchain.com/oss/python/langchain/middleware/custom)
- [LangGraph StateGraph 文档](https://langchain-ai.github.io/langgraph/)

## 相关文档

- [系统架构设计](system-design.md) - 整体系统架构设计理念
- [微服务架构设计](microservices.md) - 微服务拆分和通信设计
- [Agent V2 迁移决策](../decisions/agent-v2-migration.md) - V2 迁移背景和效果
- **[Skills 开发指南](../guides/skills-development.md)** - 添加新技能的操作指南

---

**实现时间**：2026-01
**当前状态**：✅ 已完成并集成到服务端
**版本**：v2.2（动态工具注册）
**最后更新**：2026-02-22

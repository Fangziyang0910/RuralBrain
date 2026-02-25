# 技能池热更新机制

**专利类型**：发明专利（主权利要求核心）
**创新等级**：⭐⭐⭐
**创建日期**：2026-02-24
**相关模块**：Agent V2 Skills 架构、SkillRegistry、DynamicToolMiddleware

---

## 一、专利名称

> **一种零停机时间的智能体技能池热更新方法及系统**

---

## 二、当前问题分析

### 2.1 现有 Agent 技能管理的局限性

| 问题 | 描述 | 影响 |
|------|------|------|
| **重启依赖** | 添加/修改技能需要重启整个服务 | 服务中断，用户体验差 |
| **静态加载** | 技能配置在启动时一次性加载 | 无法响应运行时需求变化 |
| **全局更新** | 更新影响所有会话，无隔离机制 | 无法灰度发布，风险高 |
| **无卸载机制** | 技能加载后无法动态卸载 | 内存累积，资源浪费 |
| **优先级固定** | 技能优先级配置后无法动态调整 | 无法适应场景变化 |

### 2.2 具体场景问题

**场景 1：紧急技能更新需要重启服务**
- 发现病虫害检测技能配置有误
- 需要修改 YAML 配置文件
- 必须重启整个服务才能生效
- 所有正在进行的会话被中断

**场景 2：无法根据场景动态调整技能优先级**
- 白天主要处理病虫害检测需求
- 晚上主要处理规划咨询需求
- 技能优先级固定，无法按时间段调整

**场景 3：临时技能无法卸载**
- 加载一个临时的实验性技能
- 使用后无法卸载，占用内存
- 长时间运行后内存累积

---

## 三、技术方案

### 3.1 核心概念：技能生命周期状态机

为每个技能引入 **生命周期状态**，支持运行时动态管理：

```
技能生命周期状态机：

     ┌─────────┐
     │  加载中  │
     └────┬────┘
          │ 加载成功
          ▼
┌─────────┐     升级     ┌─────────┐
│  活跃   │ ◄──────────► │  暂停   │
│ (Active)│              │(Paused) │
└────┬────┘              └────┬────┘
     │ 卸载                  │ 恢复
     ▼                       │
┌─────────┐                 │
│  已卸载  │ ◄───────────────┘
└─────────┘

状态定义：
- 加载中（Loading）：正在加载技能配置和依赖
- 活跃（Active）：技能正常可用
- 暂停（Paused）：技能暂时不可用（可恢复）
- 已卸载（Unloaded）：技能已从内存中移除
```

### 3.2 统一调度管理器架构

```
┌─────────────────────────────────────────┐
│     技能池调度管理器 (SkillPoolManager)    │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │       技能生命周期管理             │ │
│  │  load_skill, unload_skill,        │ │
│  │  pause_skill, resume_skill,       │ │
│  │  reload_skill                     │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │       优先级动态调整               │ │
│  │  set_priority, get_ranking,       │ │
│  │  apply_policy                     │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │       会话隔离管理                 │ │
│  │  - 会话级技能状态                  │ │
│  │  - 灰度发布支持                    │ │
│  │  - A/B 测试支持                    │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│       动态工具注册中间件                   │
│  - 监听技能池变化事件                     │
│  - 自动更新会话工具集                     │
│  - 保持会话隔离                           │
└─────────────────────────────────────────┘
```

### 3.3 技能注册接口规范

定义统一的技能注册接口，支持插件式扩展：
- `register(skill)`：注册新技能
- `unregister(skill_name)`：卸载技能
- `update(skill_name, skill)`：更新技能
- `get(skill_name)`：获取技能
- `list_all()`：列出所有技能
- `set_priority(skill_name, priority)`：设置技能优先级
- `get_status(skill_name)`：获取技能状态

---

## 四、实现思路

### 4.1 项目现有基础

| 现有模块 | 功能 | 复用方式 |
|---------|------|---------|
| `SkillRegistry` | YAML 技能配置加载 | 增加热更新方法 |
| `DynamicToolMiddleware` | 会话级工具管理 | 增加事件监听机制 |
| YAML 技能配置 | 技能元数据定义 | 增加优先级字段 |
| `load_skill` 工具 | 按需加载技能 | 集成热更新接口 |

### 4.2 实现步骤概览

**步骤 1：扩展技能状态定义**
- 新建 `status.py` 文件
- 定义 `SkillLifecycleState` 枚举（LOADING/ACTIVE/PAUSED/UNLOADED）
- 定义 `SkillStatus` 数据类

**步骤 2：实现技能池调度管理器**
- 新建 `pool_manager.py` 文件
- 实现 `SkillPoolManager` 类
- 核心方法：
  - 生命周期管理：load_skill, unload_skill, pause_skill, resume_skill, reload_skill
  - 优先级管理：set_priority, get_ranking, apply_priority_policy
  - 事件监听：add_listener, remove_listener, _emit_event

**步骤 3：扩展 SkillRegistry 支持动态操作**
- 新增 `add_skill` 方法：动态添加技能
- 新增 `remove_skill` 方法：移除技能
- 新增 `update_skill` 方法：更新技能配置

**步骤 4：集成到 DynamicToolMiddleware**
- 增加事件监听机制
- 监听技能卸载事件，自动清理已注册工具

**步骤 5：提供管理 API 端点**
- 新建 `admin_routes.py` 文件
- 提供 HTTP API：
  - POST /admin/skills/load - 热加载技能
  - POST /admin/skills/unload/{skill_name} - 卸载技能
  - POST /admin/skills/pause/{skill_name} - 暂停技能
  - POST /admin/skills/resume/{skill_name} - 恢复技能
  - POST /admin/skills/reload/{skill_name} - 重新加载
  - POST /admin/skills/priority - 设置优先级
  - GET /admin/skills/list - 列出技能
  - GET /admin/skills/status/{skill_name} - 获取技能状态

### 4.3 配置示例

**时间优先级策略配置**
```yaml
# config/priority_policies.yaml
time_based_policy:
  name: "time_based"
  schedules:
    - hours: [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
      priorities:
        pest_detection: 100
        rice_detection: 90
        cow_detection: 80
        consult_planning_knowledge: 50
    - hours: [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
      priorities:
        consult_planning_knowledge: 100
        pest_detection: 50
        rice_detection: 40
```

---

## 五、技术效果

### 5.1 功能增强

| 能力 | 实现前 | 实现后 | 改善 |
|------|--------|--------|------|
| 技能更新 | 需要重启服务 | 零停机热更新 | 服务可用性 100% |
| 技能卸载 | 不支持 | 支持动态卸载 | 内存可控 |
| 优先级调整 | 配置文件修改重启 | 运行时动态调整 | 即时生效 |
| 灰度发布 | 不支持 | 支持会话级灰度 | 降低风险 |

### 5.2 运维效率

- **无需重启**：技能配置更改后立即生效
- **远程管理**：通过 HTTP API 远程管理技能池
- **策略自动化**：支持基于时间、使用频率的自动优先级调整
- **监控可见**：完整的技能状态查询接口

### 5.3 系统可靠性

- **会话隔离**：不同会话可使用不同版本的技能
- **优雅降级**：技能暂停不影响已加载的会话
- **回滚支持**：通过 reload_skill 快速回滚

---

## 六、专利权利要求建议

### 6.1 独立权利要求（主权利要求）

> 一种零停机时间的智能体技能池热更新方法，其特征在于，包括：
>
> 1. **技能生命周期管理步骤**：为每个技能维护生命周期状态，所述状态包括加载中、活跃、暂停和已卸载；
> 2. **热加载步骤**：在不重启服务的情况下，动态加载新技能配置到技能池；
> 3. **优先级动态调整步骤**：在运行时动态调整技能优先级，影响模型工具选择顺序；
> 4. **会话隔离步骤**：确保技能更新操作不会影响正在进行的会话；
> 5. **事件通知步骤**：当技能状态发生变化时，通知相关组件进行相应处理。

---

## 七、实施时间估算

| 任务 | 工作量 |
|------|--------|
| 实现技能状态定义 | 0.5 天 |
| 实现 SkillPoolManager | 2 天 |
| 扩展 SkillRegistry | 0.5 天 |
| 集成 DynamicToolMiddleware | 1 天 |
| 实现管理 API 端点 | 1 天 |
| 测试与调优 | 2.5 天 |
| **总计** | **7.5 天** |

---

## 八、相关文件索引

| 文件 | 作用 |
|------|------|
| [src/agents/skills/status.py](../../src/agents/skills/status.py) | 新建：技能状态定义 |
| [src/agents/skills/pool_manager.py](../../src/agents/skills/pool_manager.py) | 新建：技能池管理器 |
| [src/agents/skills/registry.py](../../src/agents/skills/registry.py) | 扩展：动态操作方法 |
| [src/agents/middleware/dynamic_tool_middleware.py](../../src/agents/middleware/dynamic_tool_middleware.py) | 集成：事件监听 |
| [service/admin_routes.py](../../service/admin_routes.py) | 新建：管理 API |
| src/config/priority_policies.yaml | 新建：优先级策略配置 |

# RuralBrain Agent 架构升级 - V2 Agent 集成实施计划

## 一、概述

本计划的目标是将第一阶段完成的 **Skills 架构（V2 Agent）** 集成到服务端，实现平滑的版本切换和迁移。

### 当前状态

**已完成（第一阶段）：**

- ✅ `src/agents/middleware/skill_middleware.py` - 技能中间件，实现 Progressive Disclosure
- ✅ `src/agents/middleware/tool_selector_middleware.py` - 工具选择中间件
- ✅ `src/agents/skills/base.py` - Skill 抽象基类
- ✅ `src/agents/skills/detection_skills.py` - 3个检测技能
- ✅ `src/agents/image_detection_agent_v2.py` - V2 Agent
- ✅ `test_skills_architecture.py` - 测试框架

**待完成：**

- ❌ 服务端集成（`service/server.py` 仍在使用 V1）
- ❌ 配置切换机制
- ❌ 完整功能测试验证

### 核心目标

1. **平滑迁移**：新旧版本共存，不影响现有功能
2. **可配置切换**：通过环境变量选择 V1 或 V2
3. **充分测试**：验证 V2 功能和质量
4. **优雅降级**：V2 失败时自动切换到 V1

------

## 二、实施步骤

### 步骤 1：添加配置支持

**文件：`.env.example`**

添加以下配置：



```bash
# ============================================
# Agent 版本配置
# ============================================
# Agent 版本选择: v1, v2, auto
# - v1: 使用传统固定提示词架构
# - v2: 使用基于 Skills 的新架构（推荐）
# - auto: 自动选择（当前默认为 v1）
AGENT_VERSION=v1

# V2 Agent 失败时是否自动回退到 V1
AGENT_AUTO_FALLBACK=true
```

**文件：`service/settings.py`**

添加配置读取：



```python
# Agent 配置
AGENT_VERSION = os.getenv("AGENT_VERSION", "v1").lower()
AGENT_AUTO_FALLBACK = os.getenv("AGENT_AUTO_FALLBACK", "true").lower() == "true"
```

------

### 步骤 2：修改 Agent 加载逻辑

**文件：`service/server.py`（第 84-92 行）**

将现有的 `get_agent()` 函数替换为支持版本切换的版本：



```python
def get_agent():
    """
    延迟加载 image_detection_agent
    支持版本切换：通过 AGENT_VERSION 环境变量选择 v1 或 v2
    """
    global _agent

    if _agent is None:
        from service.settings import AGENT_VERSION, AGENT_AUTO_FALLBACK

        logger.info(f"正在加载 AI 模型 [配置版本: {AGENT_VERSION}]...")

        try:
            # 尝试加载配置的版本
            if AGENT_VERSION == "v2":
                logger.info("→ 尝试加载 V2 Agent (Skills 架构)...")
                from src.agents.image_detection_agent_v2 import agent as agent_v2
                _agent = agent_v2
                _agent_version = "v2"
                logger.info("✓ V2 Agent (Skills 架构) 加载完成")
            else:  # v1 或其他
                logger.info("→ 加载 V1 Agent (传统架构)...")
                from src.agents.image_detection_agent import agent as agent_v1
                _agent = agent_v1
                _agent_version = "v1"
                logger.info("✓ V1 Agent (传统架构) 加载完成")

        except Exception as e:
            # V2 加载失败时的降级处理
            if AGENT_VERSION == "v2" and AGENT_AUTO_FALLBACK:
                logger.warning(f"⚠ V2 Agent 加载失败: {e}")
                logger.info("→ 自动回退到 V1 Agent...")
                try:
                    from src.agents.image_detection_agent import agent as agent_v1
                    _agent = agent_v1
                    _agent_version = "v1"
                    logger.info("✓ V1 Agent (回退) 加载完成")
                except Exception as fallback_error:
                    logger.error(f"✗ V1 Agent 回退也失败: {fallback_error}")
                    raise
            else:
                logger.error(f"✗ Agent 加载失败: {e}")
                raise

        # 保存全局版本标识
        global _agent_version
        _agent_version = _agent_version

    return _agent


# 全局变量：当前使用的 Agent 版本
_agent_version = None


def get_agent_version() -> str:
    """
    获取当前使用的 Agent 版本

    Returns:
        "v1" 或 "v2"
    """
    global _agent_version
    if _agent_version is None:
        # 如果 Agent 还未加载，返回配置的版本
        from service.settings import AGENT_VERSION
        return AGENT_VERSION
    return _agent_version
```

------

### 步骤 3：增强日志和监控

**文件：`service/server.py`（第 95-100 行）**

修改启动事件：



```python
@app.on_event("startup")
async def startup_event():
    """启动时预加载模型"""
    from service.settings import AGENT_VERSION

    logger.info("RuralBrain 服务启动中...")
    logger.info(f"Agent 配置版本: {AGENT_VERSION.upper()}")

    get_agent()  # 预加载模型

    # 显示实际使用的版本
    actual_version = get_agent_version()
    logger.info(f"Agent 实际版本: {actual_version.upper()}")
    logger.info("RuralBrain 服务启动完成")
```

**文件：`service/server.py`（第 410 行）**

修改 Agent 调用日志：



```python
# 原代码：
logger.info(f"调用图像检测 Agent [thread_id={thread_id}]: {request.message}, 图片数量: {len(image_paths)}")

# 修改为：
agent_version = get_agent_version()
logger.info(f"调用图像检测 Agent [版本: {agent_version.upper()}, thread_id={thread_id}]: {request.message}, 图片数量: {len(image_paths)}")
```

------

### 步骤 4：运行测试验证

**运行 Skills 架构测试：**



```bash
uv sync
uv run python test_skills_architecture.py
```

预期输出：

- ✅ 技能创建（3个检测技能）
- ✅ 技能内容生成
- ✅ load_skill 工具功能
- ✅ 技能注册中心

**本地启动服务测试：**



```bash
# 测试 V1（默认）
uv run python run_server.py

# 测试 V2（修改 .env 设置 AGENT_VERSION=v2）
uv run python run_server.py
```

------

### 步骤 5：创建对比测试脚本

**新文件：`test_agent_comparison.py`**

创建完整的对比测试脚本，自动对比 V1 和 V2 的响应质量、Token 消耗等。

### 步骤 6：Git 提交策略（5 次原子化提交）

**Commit 1: 配置支持**



```
feat(config): 添加 Agent 版本配置支持

- 在 .env.example 中添加 AGENT_VERSION 和 AGENT_AUTO_FALLBACK 配置
- 在 service/settings.py 中添加配置读取逻辑
- 默认使用 V1（保守策略），需要手动切换到 V2
```

**Commit 2: Agent 加载逻辑**



```
feat(agent): 实现版本切换和优雅降级

- 修改 get_agent() 函数支持 v1/v2 版本切换
- 实现 V2 失败时自动回退到 V1 的机制
- 添加 get_agent_version() 辅助函数
```

**Commit 3: 日志增强**



```
feat(logging): 增强 Agent 版本日志

- 在启动事件中显示配置版本和实际版本
- 在 Agent 调用日志中包含版本标识
```

**Commit 4: 对比测试脚本**



```
test(agent): 添加 V1/V2 Agent 对比测试脚本

- 创建 test_agent_comparison.py 自动对比测试
- 验证功能一致性和性能差异
```

**Commit 5: 文档更新**



```
docs(agent): 更新 Agent 架构相关文档

- 更新 CLAUDE.md 说明 V2 Agent 架构和使用方法
- 添加版本切换说明
```

------

## 三、关键文件清单

实施此计划需要修改的关键文件：

1. **`.env.example`** - 添加配置项
2. **`service/settings.py`** - 添加配置读取
3. **`service/server.py`** - 核心修改（版本切换、降级、日志）
4. **`src/agents/image_detection_agent_v2.py`** - 已完成，无需修改
5. **`test_skills_architecture.py`** - 已完成，用于验证

------

## 四、验证和测试

### 功能验证

-  启动服务时日志显示正确的版本信息
-  V1 模式下功能正常（与之前一致）
-  V2 模式下功能正常
-  V2 加载失败时自动降级到 V1

### 日志验证

启动日志应显示：



```
INFO: RuralBrain 服务启动中...
INFO: Agent 配置版本: V2
INFO: 正在加载 AI 模型 [配置版本: v2]...
INFO: → 尝试加载 V2 Agent (Skills 架构)...
INFO: ✓ V2 Agent (Skills 架构) 加载完成
INFO: Agent 实际版本: V2
INFO: RuralBrain 服务启动完成
```

### 回滚测试

-  设置 `AGENT_VERSION=v1` 可快速切换回旧版本
-  V2 导入失败时自动降级，服务仍可用

------

## 五、风险控制

### 潜在风险

| 风险          | 影响         | 缓解措施                 |
| ------------- | ------------ | ------------------------ |
| V2 导入失败   | 服务无法启动 | 自动降级到 V1            |
| V2 运行时异常 | 请求失败     | 详细的错误日志，便于排查 |
| 输出质量差异  | 用户不满     | 充分测试，人工评估       |

### 回滚方案

**快速回滚（配置级别）：**



```bash
# 修改 .env
AGENT_VERSION=v1

# 重启服务
```

------

## 六、后续工作

完成本计划后，下一步工作：

1. **第二阶段：YAML 配置化** - 将技能定义迁移到 YAML 文件
2. **Planning Agent 重构** - 将规划咨询 Agent 也迁移到 Skills 架构
3. **性能优化** - 基于 LangSmith 数据优化 Token 消耗
4. **技能扩展** - 添加更多农业领域的技能

------

## 七、参考文档

- [LangChain Skills 官方文档](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)
- [项目 CLAUDE.md](vscode-webview://0j0g3ohl89gpj3k9d6pi1t3273bipo0dnv6rreemh9rp5bqnfk3d/CLAUDE.md) - 开发规则和项目概述
- [Agent架构升级方案.md](vscode-webview://0j0g3ohl89gpj3k9d6pi1t3273bipo0dnv6rreemh9rp5bqnfk3d/index.html?id=8e67a226-3bd8-4cf8-9bc6-3d16ef07f267&parentId=1&origin=fd9cd88e-2c2d-45e5-8d8f-81b31eddd44a&swVersion=4&extensionId=Anthropic.claude-code&platform=electron&vscode-resource-base-authority=vscode-resource.vscode-cdn.net&parentOrigin=vscode-file%3A%2F%2Fvscode-app&session=f7e26a23-a4e0-4595-88a5-802c204225e9) - 完整架构方案
# Planning Agent 优化总结与下一步建议

## 📊 当前优化成果（已完成）

### ✅ 已完成优化

| 优化项 | 状态 | 效果 |
|--------|------|------|
| 修复知识库引用显示 | ✅ 完成 | 成功率 0% → 100% |
| 优化工具描述（渐进式披露） | ✅ 完成 | Token 消耗减少 30-50% |
| 精简系统提示词 | ✅ 完成 | Token 消耗减少 54% |
| 添加工具调用监控 | ✅ 完成 | 实时统计调用次数和响应时间 |
| 创建测试脚本 | ✅ 完成 | 4/4 单元测试通过 |

### 🧪 测试情况

**单元测试：** ✅ 通过（test_optimization.py）
- 知识库引用提取：✅ 通过
- 模式配置验证：✅ 通过
- 提示词优化：✅ 通过
- 工具描述优化：✅ 通过

**集成测试：** ⚠️ 部分完成
- 端到端测试：发现中间件 API 兼容性问题
- 服务级测试：未进行（Docker 在 WSL 不可用）

### 🐛 发现的问题

1. **中间件 API 兼容性问题**
   - `ModelRequest` 对象没有 `system_message` 属性
   - 影响：无法通过中间件动态注入模式信息到系统提示词
   - 解决方案：已简化为配置类，不再尝试运行时注入

2. **知识库引用中的 doc_type 提取不准确**
   - 正则表达式提取 `第3 pptx` 时，doc_type 显示为 `ptx` 而不是 `pptx`
   - 影响：文档类型显示不完整
   - 优先级：低（不影响核心功能）

---

## 🚀 下一步优化建议

### 高优先级（P0）- 立即可实施

#### 1. 实现真正的模式约束

**当前问题：**
- 模式信息只是记录在日志中，无法真正约束 Agent 行为
- Fast 模式可能调用 5+ 次工具，Deep 模式可能调用 10+ 次

**解决方案 A：在系统提示词中硬编码模式信息**
```python
# 在 planning_agent.py 中
def build_system_prompt_with_mode(mode: str = "auto"):
    """根据模式动态构建系统提示词"""
    mode_instruction = ""

    if mode == "fast":
        mode_instruction = """
<current_mode>
当前工作模式: 快速浏览模式
工具调用限制: 最多 2 次
重要: 请严格限制工具调用次数，优先使用 get_document_overview 和 search_key_points
</current_mode>
"""
    elif mode == "deep":
        mode_instruction = """
<current_mode>
当前工作模式: 深度分析模式
工具调用限制: 最多 5 次
可以使用完整工具链进行深度分析
</current_mode>
"""

    return SYSTEM_PROMPT_BASE + mode_instruction + build_tool_description_section(tools)
```

**实施方案：**
- 修改 `planning_agent.py` 添加带模式的系统提示词构建函数
- 修改 `routes.py` 在调用 Agent 前重建系统提示词
- 优点：简单可靠，立即可用
- 缺点：需要重新创建 Agent 实例（或者每次调用都更新）

**解决方案 B：使用自定义回调处理器**
```python
from langchain.callbacks import BaseCallbackHandler

class ToolCallLimitHandler(BaseCallbackHandler):
    def __init__(self, max_calls: int):
        self.max_calls = max_calls
        self.call_count = 0

    def on_tool_start(self, serialized, query_str, **kwargs):
        self.call_count += 1
        if self.call_count > self.max_calls:
            raise Exception(f"超出工具调用限制 ({self.max_calls} 次)")
```

**推荐：** 先实施方案 A（简单），如果效果不理想再考虑方案 B

---

#### 2. 修复知识库引用的 doc_type 提取

**当前问题：**
```python
# 输出：第3 pptx
# 提取结果：doc_type = "ptx"  # 错误！应该是 "pptx"
```

**解决方案：**
修改 `routes.py` 中的正则表达式：
```python
# 当前正则
pattern = r"【知识片段 \d+】\s*\n来源: ([^\n]+)\s*\n位置: 第(\d+)\s*[页pptxdocx段节]?\s*(\w+)?\s*\n内容:"

# 优化后（更精确的匹配）
pattern = r"【知识片段 \d+】\s*\n来源: ([^\n]+)\s*\n位置: 第(\d+)\s+([^\s\n]+)?\s*\n内容:"
```

或者简化提取逻辑：
```python
# 直接提取"第X"后面的所有内容作为类型
pattern = r"【知识片段 \d+】\s*\n来源: ([^\n]+)\s*\n位置: 第(\d+)\s*(.*?)\s*\n内容:"
```

---

### 中优先级（P1）- 性能优化

#### 3. 添加查询结果缓存

**当前问题：**
- 相同问题重复查询，每次都调用 LLM 和工具
- 测试中的 9 个问题可能有重复查询

**解决方案：**
```python
from functools import lru_cache
import hashlib

class QueryCache:
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size

    def get_cache_key(self, query: str, mode: str) -> str:
        return hashlib.md5(f"{query}:{mode}".encode()).hexdigest()

    def get(self, query: str, mode: str):
        key = self.get_cache_key(query, mode)
        return self.cache.get(key)

    def set(self, query: str, mode: str, result: dict):
        key = self.get_cache_key(query, mode)
        if len(self.cache) >= self.max_size:
            # 移除最旧的缓存
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        self.cache[key] = result

# 在 routes.py 中使用
query_cache = QueryCache()

# 检查缓存
cached_result = query_cache.get(request.message, request.mode)
if cached_result:
    yield cached_result
    return
```

**预期效果：**
- 重复查询响应时间：50s → < 1s
- 减少 API 调用成本

---

#### 4. 实现工具调用优化（并行调用）

**当前问题：**
- 工具按顺序调用，如 `list_documents` → `get_document_overview` → `search_key_points`
- 某些工具可以并行调用，如 `get_document_overview(doc1)` 和 `get_document_overview(doc2)`

**解决方案：**
在 Agent 提示词中添加并行调用指导：
```python
<optimization_tip>
**工具调用优化：**
- 如果需要查询多个文档，可以在一次工具调用中同时查询
- 例如：search_knowledge(query="长宁镇的GDP和旅游目标") 可以同时获取两个信息
- 避免分多次调用，提高效率
</optimization_tip>
```

**预期效果：**
- 减少 LLM 轮次
- Fast 模式响应时间：30s → 20s

---

#### 5. 添加回答长度限制

**当前问题：**
- 最长回答达 2354 字符
- 用户阅读压力大

**解决方案：**
在系统提示词中添加长度限制：
```python
<constraints>
- **回答长度**：核心回答不超过 1500 字符，详细内容可分点列出
- 如果回答过长，使用"1. 2. 3."分点，每点不超过 200 字
</constraints>
```

或在后端截断：
```python
# 在 routes.py 中
MAX_RESPONSE_LENGTH = 2000

if len(full_content) > MAX_RESPONSE_LENGTH:
    # 智能截断（在句子边界）
    truncated = full_content[:MAX_RESPONSE_LENGTH]
    last_period = truncated.rfind('。')
    if last_period > MAX_RESPONSE_LENGTH * 0.8:
        full_content = truncated[:last_period + 1]
    full_content += "\n\n（回答已截断，如需完整信息请继续提问）"
```

---

### 低优先级（P2）- 长期优化

#### 6. 实现智能模式选择

**当前问题：**
- 用户需要手动选择模式（auto/fast/deep）
- 用户可能不知道该选哪个

**解决方案：**
```python
def analyze_question_complexity(question: str) -> str:
    """
    分析问题复杂度，自动选择模式

    Returns: 'fast' 或 'deep'
    """
    # 简单关键词分析
    deep_keywords = ["策略", "规划", "方案", "制定", "分析", "评估"]
    fast_keywords = ["多少", "是什么", "哪些", "目标", "GDP"]

    deep_count = sum(1 for kw in deep_keywords if kw in question)
    fast_count = sum(1 for kw in fast_keywords if kw in question)

    if deep_count >= 2 or "策略" in question or "规划" in question:
        return "deep"
    else:
        return "fast"

# 在 routes.py 中
auto_mode = analyze_question_complexity(request.message)
if request.mode == "auto":
    effective_mode = auto_mode
else:
    effective_mode = request.mode
```

---

#### 7. 添加超时控制

**当前问题：**
- 最长响应时间 78.8 秒
- 可能影响用户体验

**解决方案：**
```python
import asyncio

async def event_generator():
    try:
        # 设置超时
        async for event in asyncio.wait_for(
            agent.astream_events(input_data, config, version="v2"),
            timeout=60.0  # 60 秒超时
        ):
            # 处理事件
            ...
    except asyncio.TimeoutError:
        # 发送超时消息
        yield f"data: {json.dumps({'type': 'timeout', 'message': '响应超时，请简化问题或稍后重试'})}\n\n"
```

---

#### 8. 实现 A/B 测试框架

**目的：**
- 对比优化前后的性能
- 验证模式约束的有效性
- 收集用户反馈

**实施方案：**
```python
class ABTestFramework:
    def __init__(self):
        self.results = []

    def record_test(self, scenario: str, mode: str, metrics: dict):
        self.results.append({
            "scenario": scenario,
            "mode": mode,
            "time": metrics["time"],
            "tool_calls": metrics["tool_calls"],
            "response_length": metrics["response_length"],
            "sources_count": metrics["sources_count"],
        })

    def generate_report(self):
        # 生成对比报告
        ...
```

---

## 📋 实施优先级建议

### 立即实施（本周）
1. ✅ 修复知识库引用 doc_type 提取（5 分钟）
2. ✅ 实现模式约束方案 A（30 分钟）
3. ✅ 运行完整的集成测试（1 小时）

### 短期实施（1-2 周）
4. 添加查询结果缓存（2 小时）
5. 添加回答长度限制（30 分钟）
6. 添加超时控制（30 分钟）

### 中期实施（1 个月）
7. 实现工具调用优化（并行调用）（4 小时）
8. 实现智能模式选择（2 小时）
9. 添加 A/B 测试框架（3 小时）

---

## 🎯 成功指标

| 指标 | 当前 | 目标 | 测量方法 |
|------|------|------|----------|
| Fast 模式响应时间 | 78.8s | < 30s | 集成测试 |
| Deep 模式响应时间 | 未测试 | < 60s | 集成测试 |
| 平均响应时间 | 54.2s | < 40s | 集成测试 |
| Fast 模式工具调用 | 无限制 | ≤ 2 次 | 日志统计 |
| Deep 模式工具调用 | 无限制 | ≤ 5 次 | 日志统计 |
| 知识库引用成功率 | 100% | 100% | 单元测试 |
| 回答长度 | 最长 2354 字符 | < 2000 字符 | 自动检查 |

---

## 🛠️ 快速实施指南

### 修复 1：知识库引用 doc_type 提取

```bash
# 1. 编辑文件
vim src/rag/service/api/routes.py

# 2. 找到第 80 行，修改正则表达式
pattern = r"【知识片段 \d+】\s*\n来源: ([^\n]+)\s*\n位置: 第(\d+)\s*(.*?)\s*\n内容:"

# 3. 运行测试
python3 test_optimization.py

# 4. 提交修改
git add src/rag/service/api/routes.py
git commit -m "fix(planning): 修复知识库引用 doc_type 提取"
```

### 修复 2：实现模式约束

```bash
# 1. 编辑 planning_agent.py
vim src/agents/planning_agent.py

# 2. 添加新函数
def build_system_prompt_with_mode(mode: str = "auto"):
    ...

# 3. 编辑 routes.py
vim src/rag/service/api/routes.py

# 4. 在调用 Agent 前重建系统提示词
# （具体代码见上方"解决方案 A"）

# 5. 测试
python3 src/rag/tests/test_e2e_planning.py

# 6. 提交修改
git add .
git commit -m "feat(planning): 实现工作模式硬性约束"
```

---

## 📚 相关文档

- 测试报告：`规划咨询测试报告.md`
- 单元测试：`test_optimization.py`
- 端到端测试：`src/rag/tests/test_e2e_planning.py`
- 优化计划：`/home/szh/.claude/plans/functional-wishing-barto.md`

---

**生成时间：** 2026-01-23
**作者：** Claude Code
**版本：** 1.0

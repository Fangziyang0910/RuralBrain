# RAG 规划服务模块优化建议报告

> 生成时间：2026-02-18
> 分支：feature/knowledge-base-refactor

---

## 一、当前架构问题

### 1. 混合架构（高优先级）
- 两套工具系统共存：`src/rag/core/tools.py` 和 `src/agents/tools/planning_service_tool.py`
- 独立服务（端口 8003）与内嵌 Agent 共存
- 存在循环依赖风险

### 2. 代码重复（中优先级）
- 工具定义两种方式混用（Tool 类 vs @tool 装饰器）
- 7 个向后兼容别名冗余
- `key_points_search_tool` 和 `retrieve_knowledge` 重复逻辑

### 3. 配置分散（高优先级）
```
service/core/config.py       # 服务配置（端口 8003）
rag/config.py               # RAG 配置（向量库路径）
src/config.py               # 全局配置
```

---

## 二、性能瓶颈

| 问题 | 位置 | 影响 |
|------|------|------|
| 查询缓存未启用 | cache.py:44,59 | 重复查询无优化 |
| Embedding 模型重复加载 | cache.py:69-86 | 每次进程重启重加载 |
| 流式缓冲过小 | routes.py:182 | `BUFFER_SIZE=1`，SSE 事件过多 |
| Chroma 无连接池 | cache.py:88-106 | 并发性能差 |

---

## 三、错误处理与安全

### 错误处理问题
- 异常捕获过于宽泛（`except Exception`）
- `planning_service_tool.py` 无重试机制
- 文档加载无完整性验证

### 安全问题
- `context_manager.py:46` 存在路径遍历风险
- 输入无验证（message 无长度限制）
- 敏感信息可能泄露到日志（routes.py:224）

---

## 四、优化建议

### 阶段 1：紧急优化（性能提升 50-80%）

1. **启用查询缓存**
   - 在 `search_knowledge` 函数中集成已有的缓存机制
   - 预期延迟降低 50-80%

2. **优化流式缓冲**
   ```python
   # routes.py:182
   BUFFER_SIZE = 100  # 从 1 调整为 100
   ```

3. **统一工具定义**
   - 移除 `tools.py` 中的 `Tool()` 构造函数版本
   - 删除 7 个向后兼容别名

4. **添加请求追踪**
   ```python
   request_id = str(uuid.uuid4())
   logger.info(f"[{request_id}] 收到请求...")
   ```

### 阶段 2：重要改进

5. **合并配置文件** - 创建统一配置中心
6. **添加重试机制** - 使用 `tenacity` 库
7. **改进错误处理** - 自定义异常类，统一错误响应
8. **修复安全问题** - 路径验证、输入校验

### 阶段 3：长期优化

9. **添加性能监控** - Prometheus 指标
10. **完善测试覆盖** - 并发测试、性能基准
11. **扩展健康检查** - 依赖服务状态检查
12. **完善类型注解** - 使用 Literal、TypedDict

---

## 五、关键文件清单

| 文件 | 优先级 | 优化点 |
|------|--------|--------|
| `src/rag/core/tools.py` | 高 | 删除重复定义 |
| `src/rag/core/cache.py` | 高 | 启用查询缓存 |
| `src/rag/service/api/routes.py` | 高 | 优化缓冲、添加追踪 |
| `src/agents/tools/planning_service_tool.py` | 中 | 添加重试机制 |
| `src/rag/core/context_manager.py` | 中 | 路径验证 |

# 检测服务网关化决策

## 决策背景

### 原始架构

最初，每个检测类型是一个独立的 FastAPI 服务：

| 服务 | 端口 | 路由前缀 |
|------|------|----------|
| 病虫害检测 | 8000 | `/detect` |
| 大米品种识别 | 8001 | `/detect` |
| 奶牛检测 | 8002 | `/detect` |

### 存在的问题

1. **端口管理复杂**
   - 3 个独立端口需要分别配置和管理
   - 端口冲突风险增加
   - 文档中端口信息容易不一致

2. **客户端调用复杂**
   - Agent 需要知道每个服务的具体地址
   - 新增检测类型需要修改客户端代码
   - 错误处理分散在多个服务

3. **部署和维护成本高**
   - 3 个独立的 Docker 容器
   - 3 组独立的配置和日志
   - 统一升级困难

4. **资源利用率低**
   - 每个服务独立加载 ONNX Runtime
   - 重复的模型加载逻辑

---

## 决策方案

### 统一网关架构

将所有检测服务整合到单一网关：

```
检测服务网关 (8001)
    │
    ├─ /detection/pest/*  → 病虫害检测
    ├─ /detection/rice/*  → 大米品种识别
    ├─ /detection/cow/*   → 奶牛检测
    └─ /health            → 健康检查
```

### 实现方式

**文件**：`src/algorithms/api/main.py`

```python
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI(title="RuralBrain Detection Gateway")

# 路由分发
@app.get("/detection/pest/{path:path}")
async def redirect_pest(path: str):
    return RedirectResponse(url=f"/pest/{path}")

@app.get("/detection/rice/{path:path}")
async def redirect_rice(path: str):
    return RedirectResponse(url=f"/rice/{path}")

@app.get("/detection/cow/{path:path}")
async def redirect_cow(path: str):
    return RedirectResponse(url=f"/cow/{path}")
```

**实际实现**：各检测服务作为子应用挂载到网关

```python
from pest_service import app as pest_app
from rice_service import app as rice_app
from cow_service import app as cow_app

app.mount("/detection/pest", pest_app)
app.mount("/detection/rice", rice_app)
app.mount("/detection/cow", cow_app)
```

---

## 方案对比

| 方面 | 独立服务（原始） | 统一网关（新方案） |
|------|------------------|-------------------|
| **端口数量** | 3 个 (8000, 8001, 8002) | 1 个 (8001) |
| **容器数量** | 3 个独立容器 | 1 个容器 |
| **客户端复杂度** | 需要知道 3 个地址 | 只需知道 1 个地址 |
| **新增检测类型** | 新增服务 + 端口 + 容器 | 新增路由即可 |
| **资源占用** | 3 × ONNX Runtime | 1 × ONNX Runtime |
| **维护成本** | 高 | 低 |
| **扩展性** | 每服务独立扩展 | 整体扩展 |

---

## 实施过程

### 第一阶段：架构设计

1. 确定网关统一端口为 8001
2. 设计路由规范：`/detection/{type}/{action}`
3. 确定向后兼容方案

### 第二阶段：代码重构

1. 创建 `src/algorithms/api/main.py` 网关入口
2. 将各检测服务作为子应用挂载
3. 更新服务配置

### 第三阶段：更新调用方

1. 更新 Agent 工具中的服务地址
2. 更新文档中的端口说明
3. 更新 Docker Compose 配置

### 第四阶段：测试验证

1. 功能测试：各检测类型正常工作
2. 性能测试：响应时间无明显变化
3. 兼容性测试：旧客户端仍可访问

---

## 效果评估

### 定量改进

| 指标 | 改进 |
|------|------|
| 端口数量 | 3 → 1 (-67%) |
| Docker 容器 | 3 → 1 (-67%) |
| 配置文件 | 3 组 → 1 组 |
| 文档更新点 | 3 处 → 1 处 |

### 定性改进

1. **简化部署**
   - Docker Compose 配置更简洁
   - 启动命令统一

2. **降低维护成本**
   - 只需维护 1 个服务地址
   - 日志集中查看

3. **提升扩展性**
   - 新增检测类型只需添加路由
   - 统一的接口规范

4. **改善用户体验**
   - API 文档集中在一处
   - 服务地址更易记忆

---

## 权衡和代价

### 优点

1. 简化了架构和部署
2. 降低了维护成本
3. 提升了开发效率
4. 统一了接口规范

### 缺点

1. **单点故障风险**：网关故障影响所有检测类型
   - 缓解：健康检查和自动重启

2. **独立扩展受限**：无法单独扩展某个检测类型
   - 缓解：通过多实例部署整体扩展
   - 评估：当前规模下无需独立扩展

3. **资源竞争**：多个检测类型共享同一进程
   - 评估：ONNX Runtime 推理效率高，当前负载下无明显影响

---

## 后续优化方向

### 短期

1. 完善网关监控和日志
2. 优化健康检查机制
3. 添加性能指标收集

### 长期

1. 如果单个检测类型负载过高，考虑拆分
2. 添加服务降级和熔断机制
3. 考虑引入 API 网关（如 Kong、Traefik）

---

## 相关文档

- [系统架构设计](../architecture/system-design.md)
- [微服务架构设计](../architecture/microservices.md)
- [端口统一决策](port-unification.md)
- [统一命令参考](../commands.md)

---

**决策日期**: 2026-01-15
**决策状态**: 已实施
**效果**: 运行稳定，维护成本显著降低

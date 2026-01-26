# 端口配置变更说明

**日期**：2026-01-26
**变更原因**：统一检测服务端口分配，避免端口冲突

---

## 变更内容

### 检测服务端口调整

| 服务 | 原端口 | 新端口 | 变更原因 |
|------|--------|--------|----------|
| 病虫害检测 | 8001 | **8000** | 统一为连续端口 |
| 大米识别 | 8081 | **8001** | 与后端服务(8081)冲突，改为 8001 |
| 奶牛检测 | 8002 | **8002** | 保持不变 |

### 新的端口分配规范

```
8000: 病虫害检测服务
8001: 大米识别服务
8002: 奶牛检测服务
```

三个检测服务现在使用连续的端口编号（8000-8002），更易于管理和记忆。

---

## 修改的文件

### 1. 服务配置文件

#### 病虫害检测
**文件**：`src/algorithms/pest_detection/detector/app/core/config.py`
```python
# 修改前
PORT: int = 8001

# 修改后
PORT: int = 8000  # 病虫害检测服务
```

#### 大米识别
**文件**：`src/algorithms/rice_detection/detector/app/core/config.py`
```python
# 修改前
PORT: int = 8081

# 修改后
PORT: int = 8001  # 大米识别服务
```

#### 奶牛检测
**文件**：`src/algorithms/cow_detection/detector/app/core/config.py`
```python
# 无需修改，已经是 8002
PORT: int = 8002
```

### 2. 后端调用配置

**文件**：`src/agents/skills/detection_skills.py`

```python
# 病虫害检测 metadata
# 修改前
"service_url": "http://localhost:8001"

# 修改后
"service_url": "http://localhost:8000"  # 病虫害检测服务

# 大米识别 metadata
# 修改前
"service_url": "http://localhost:8081"

# 修改后
"service_url": "http://localhost:8001"  # 大米识别服务

# 奶牛检测 metadata
# 保持不变
"service_url": "http://localhost:8002"
```

---

## 影响范围

### 不受影响的部分
- ✅ 后端主服务端口 8081（保持不变）
- ✅ 前端服务端口 3000（保持不变）
- ✅ Docker 部署配置（使用内部网络）
- ✅ 已启动的服务（需要重启后生效）

### 需要更新的部分
- ⚠️ **手动启动的检测服务**：需要使用新的配置重新启动
- ⚠️ **API 文档书签**：如果保存了旧端口的文档链接，需要更新
- ⚠️ **前端硬编码**：前端没有硬编码检测服务地址（通过后端转发），无需修改

---

## 迁移步骤

### 1. 停止所有服务
```bash
bash scripts/dev/stop_all_services.sh
```

### 2. 验证配置文件已更新
```bash
# 检查配置
grep "PORT.*=" src/algorithms/pest_detection/detector/app/core/config.py
grep "PORT.*=" src/algorithms/rice_detection/detector/app/core/config.py
grep "PORT.*=" src/algorithms/cow_detection/detector/app/core/config.py

# 检查调用配置
grep "service_url" src/agents/skills/detection_skills.py
```

### 3. 重新启动服务
```bash
# 使用新的启动脚本
bash scripts/dev/start_all_services.sh

# 或快速启动（仅后端）
bash scripts/dev/quick_start.sh
```

### 4. 验证服务状态
```bash
# 检查服务
bash scripts/dev/check_services.sh

# 手动验证
curl http://localhost:8000/docs  # 病虫害检测
curl http://localhost:8001/docs  # 大米识别
curl http://localhost:8002/docs  # 奶牛检测
curl http://localhost:8081/docs  # 后端服务
```

---

## 测试验证

### 端口连通性测试
```bash
# 测试所有检测服务
for port in 8000 8001 8002 8081; do
    echo "测试端口 $port..."
    curl -s http://localhost:$port/docs | grep -o "<title>.*</title>"
done
```

### 功能测试
```bash
# 测试病虫害检测
python scripts/test_detection.py

# 测试完整流程
python scripts/test_four_scenarios.py
```

---

## 回滚方案

如果需要回滚到旧端口配置：

### 1. 修改配置文件
```python
# 病虫害检测：8000 → 8001
# 大米识别：8001 → 8081
```

### 2. 修改调用配置
```python
# detection_skills.py
"service_url": "http://localhost:8001"  # 病虫害
"service_url": "http://localhost:8081"  # 大米
```

### 3. 重启服务
```bash
bash scripts/dev/stop_all_services.sh
bash scripts/dev/start_all_services.sh
```

---

## 常见问题

### Q1: 修改后服务无法启动？
**A**: 确保端口未被占用：
```bash
lsof -ti :8000  # 检查 8000
lsof -ti :8001  # 检查 8001
```

### Q2: 后端无法连接检测服务？
**A**: 检查 `src/agents/skills/detection_skills.py` 中的端口配置是否正确。

### Q3: 为什么要改端口？
**A**:
1. 统一检测服务端口为连续编号（8000-8002），便于管理
2. 解决大米识别服务（8081）与后端服务（8081）的冲突
3. 符合端口分配规范

### Q4: 需要更新前端代码吗？
**A**: 不需要。前端通过后端服务（8081）统一调用，不直接访问检测服务。

---

## 相关文档

- [服务管理指南](SERVICE_MANAGEMENT_GUIDE.md)
- [项目结构指南](PROJECT_STRUCTURE_GUIDE.md)
- [工作进展报告](WORK_PROGRESS_2026-01-26.md)

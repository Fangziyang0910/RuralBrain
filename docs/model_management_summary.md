# 模型管理系统实现总结

## 已完成的工作

### 1. ✅ 安装依赖包
- 添加 `langchain-zhipuai>=0.0.1` 到 `pyproject.toml`
- 已安装必要的依赖包

### 2. ✅ 创建配置模块 (`src/config.py`)
- 定义模型供应商类型 `ModelProvider`
- 配置默认供应商和温度参数
- 提供模型配置映射 `MODEL_CONFIGS`
- 支持的供应商:
  - `deepseek`: DeepSeek API
  - `glm`: 智谱AI (使用 OpenAI 兼容接口)

### 3. ✅ 创建模型管理类 (`src/utils/model_manager.py`)
- 实现通用的 `ModelManager` 类
- 支持多种初始化方式:
  - `ModelManager(provider="deepseek")` - 指定供应商
  - `ModelManager.from_env()` - 从环境变量加载
- 提供统一的模型获取接口 `get_chat_model()`
- 支持自定义参数 (temperature, model name等)

### 4. ✅ 环境配置文件 (`.env.example`)
- 提供完整的环境变量配置示例
- 包含所有供应商的 API Key 配置说明
- 包含可选的 LangSmith 配置

### 5. ✅ 更新 `image_detection_agent.py`
- 使用 `ModelManager` 替换硬编码的模型初始化
- 支持运行时动态切换模型供应商
- 在 SummarizationMiddleware 中也使用统一的模型管理

### 6. ✅ 文档和测试
- 创建详细的使用文档 (`docs/model_management.md`)
- 创建测试脚本 (`tests/test_model_manager.py`)
- 验证模块导入和基本功能正常

## 技术实现要点

### 智谱AI集成方式
由于 `langchain-zhipuai` 包功能有限,我们采用了智谱AI提供的 **OpenAI 兼容 API**:
```python
ChatOpenAI(
    model="glm-4",
    api_key=api_key,
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    ...
)
```

### 设计模式
- **工厂模式**: `ModelManager` 根据供应商名称创建不同的模型实例
- **策略模式**: 不同供应商有不同的创建策略
- **单一职责**: 配置、管理、使用分离

### 可扩展性
添加新供应商只需:
1. 在 `src/config.py` 的 `MODEL_CONFIGS` 中添加配置
2. 在 `ModelManager` 中添加对应的 `_create_xxx_model` 方法
3. 在 `.env.example` 中添加环境变量说明

## 使用方式

### 基本用法
```python
from src.utils import ModelManager

# 从环境变量自动加载
manager = ModelManager.from_env()
model = manager.get_chat_model()
```

### 切换模型
编辑 `.env` 文件:
```bash
# 使用 DeepSeek
MODEL_PROVIDER=deepseek

# 使用智谱AI
MODEL_PROVIDER=glm
```

### 运行时切换
```powershell
# Windows PowerShell
$env:MODEL_PROVIDER="glm"; python main.py
```

## 下一步建议

### 前端集换模型
未来可以通过以下方式实现前端切换:

1. **方案一: 配置文件**
   - 前端提供设置页面
   - 修改配置文件或数据库
   - 重启后端服务

2. **方案二: 运行时切换**
   - 使用 LangChain 的动态模型中间件
   - 在请求中传递模型参数
   - 示例:
   ```python
   from langchain.agents.middleware import wrap_model_call
   
   @wrap_model_call
   def dynamic_model_selection(request, handler):
       provider = request.state.get("model_provider", "deepseek")
       manager = ModelManager(provider=provider)
       model = manager.get_chat_model()
       return handler(request.override(model=model))
   ```

3. **方案三: 多 Agent 实例**
   - 预先创建多个 agent 实例 (每个使用不同模型)
   - 根据用户选择路由到不同的 agent
   - 适合需要同时支持多种模型的场景

## 验证测试

运行测试脚本验证功能:
```powershell
cd "D:\sourse code\RuralBrain"
$env:PYTHONPATH="D:\sourse code\RuralBrain"
uv run python tests/test_model_manager.py
```

## 参考文档
- 详细使用指南: `docs/model_management.md`
- 配置示例: `.env.example`
- 测试代码: `tests/test_model_manager.py`

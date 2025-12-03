# 模型管理使用指南

## 概述

RuralBrain 现在支持通用的模型管理系统,可以轻松地在不同的大语言模型供应商之间切换。

## 支持的模型供应商

- **DeepSeek**: `deepseek` - 使用 DeepSeek 原生 API
- **智谱AI (GLM)**: `glm` - 使用 OpenAI 兼容 API 接口

> 注意: 智谱AI 使用 OpenAI 兼容的 API 接口,通过 `ChatOpenAI` 类实现,自动配置正确的 base_url

## 配置方式

### 1. 环境变量配置

复制 `.env.example` 文件为 `.env`,并填入相应的配置:

```bash
# 设置默认使用的模型供应商
MODEL_PROVIDER=deepseek  # 或 glm

# 设置模型温度参数
MODEL_TEMPERATURE=0

# DeepSeek API密钥
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 智谱AI API密钥
ZHIPUAI_API_KEY=your_zhipuai_api_key_here
```

### 2. 在代码中使用

#### 方式一: 从环境变量自动加载(推荐)

```python
from src.utils import ModelManager

# 从环境变量 MODEL_PROVIDER 读取供应商配置
model_manager = ModelManager.from_env()
model = model_manager.get_chat_model()
```

#### 方式二: 手动指定供应商

```python
from src.utils import ModelManager

# 使用 DeepSeek
model_manager = ModelManager(provider="deepseek")
model = model_manager.get_chat_model()

# 使用智谱AI
model_manager = ModelManager(provider="glm")
model = model_manager.get_chat_model()
```

#### 方式三: 自定义模型参数

```python
from src.utils import ModelManager

model_manager = ModelManager(provider="deepseek")

# 使用自定义参数
model = model_manager.get_chat_model(
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=2000
)
```

#### 方式四: 手动传入 API Key

```python
from src.utils import ModelManager

model_manager = ModelManager(
    provider="glm",
    api_key="your_api_key_here"
)
model = model_manager.get_chat_model()
```

## 在 Agent 中使用

`image_detection_agent.py` 已更新为使用模型管理器:

```python
from src.utils import ModelManager

# 自动从环境变量读取配置
model_manager = ModelManager.from_env()
model = model_manager.get_chat_model()

# 在 agent 中使用
agent = create_agent(
    model=model,
    tools=[...],
    system_prompt=SYSTEM_PROMPT,
)
```

## 切换模型

### 方法一: 修改环境变量

编辑 `.env` 文件,修改 `MODEL_PROVIDER` 的值:

```bash
# 切换到 DeepSeek
MODEL_PROVIDER=deepseek

# 切换到智谱AI
MODEL_PROVIDER=glm
```

然后重启应用即可。

### 方法二: 运行时切换

在启动应用前临时设置环境变量:

**Windows PowerShell:**
```powershell
$env:MODEL_PROVIDER="glm"; python main.py
```

**Linux/Mac:**
```bash
MODEL_PROVIDER=glm python main.py
```

## 模型配置

各供应商的默认模型配置在 `src/config.py` 中定义:

```python
MODEL_CONFIGS = {
    "deepseek": {
        "default_model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "glm": {
        "default_model": "glm-4",
        "api_key_env": "ZHIPUAI_API_KEY",
    },
}
```

## 扩展新的模型供应商

要添加新的模型供应商,按以下步骤操作:

1. 安装对应的 langchain 集成包
2. 在 `src/config.py` 的 `MODEL_CONFIGS` 中添加配置
3. 在 `src/utils/model_manager.py` 中添加对应的创建方法
4. 在 `.env.example` 中添加环境变量说明

## 故障排查

### 问题: 提示找不到 API Key

**解决方案:**
- 检查 `.env` 文件是否存在且配置正确
- 确认对应的环境变量名称正确(DEEPSEEK_API_KEY 或 ZHIPUAI_API_KEY)
- 确保在 `main.py` 中已调用 `load_dotenv()`

### 问题: 不支持的供应商

**解决方案:**
- 检查 `MODEL_PROVIDER` 的值是否为 "deepseek" 或 "glm"
- 注意供应商名称区分大小写,应使用小写

### 问题: 模型调用失败

**解决方案:**
- 验证 API Key 是否有效
- 检查网络连接
- 查看模型名称是否正确(如 "deepseek-chat" 或 "glm-4")

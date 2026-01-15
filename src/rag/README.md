# RAG 知识库构建工具

## 📚 概述

这是为 **RuralBrain 乡村复杂决策智能体（Planning Agent）** 优化的知识库构建工具。

### 与传统 RAG 的区别

| 特性 | 传统 RAG | 本工具（Planning Agent 优化） |
|------|----------|------------------------------|
| **使用场景** | 问答系统 | 复杂决策规划 |
| **切片大小** | 500-1000 字符 | 2500 字符（保留更多上下文） |
| **检索数量** | 3-5 个片段 | 5-10 个片段（更全面） |
| **目标** | 快速找到精确答案 | 提供整体视图辅助决策 |
| **检索模式** | 单次检索 | Agentic RAG（LLM 自主决定） |

## ✨ 核心特性

### 1. 部署化支持
- ✅ Docker 容器化构建
- ✅ 环境变量配置
- ✅ 支持多种向量数据库（Chroma/FAISS/Qdrant）

### 2. 切片可视化
- ✅ 实时查看切片内容和统计
- ✅ 自动检测冗余和垃圾信息
- ✅ 导出分析报告（JSON）

### 3. Planning Agent 优化
- ✅ 更大的 chunk_size（2500）保留上下文
- ✅ Agentic RAG 模式支持
- ✅ 元数据过滤检索

## 🚀 快速开始

### 本地开发

#### 1. 安装依赖
```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -r requirements.txt
```

#### 2. 准备文档

**目录结构:**
```
src/data/
├── policies/           # 政策文件目录
│   ├── 2024-广东省乡村振兴政策.md
│   └── 博罗县农业发展规划.txt
└── cases/              # 案例文件目录
    ├── 智慧农业-典型案例.md
    └── 罗浮山旅游-成功案例.md
```

**支持的格式:**
- ✅ **Markdown (.md)** - 强烈推荐，保留结构，切片质量最好
- ✅ **Text (.txt)** - 备选，简单文本
- ✅ **PowerPoint (.pptx)** - 自动提取内容并转换为 Markdown
- ✅ **PDF (.pdf)** - 自动提取内容并转换为 Markdown
- ✅ **Word (.docx)** - 自动提取内容并转换为 Markdown

**重要特性：**
- 所有格式都会自动转换为统一的 Markdown 格式
- 自动清理页眉页脚、模板占位符等冗余信息
- 去除过多空白行和特殊字符
- 保留文档结构和标题层级

**详细指南:** 查看 `src/data/README.md` 了解数据处理最佳实践

#### 3. 构建知识库
```bash
# 运行构建脚本
python src/rag/build.py

# 或使用 uv
uv run python src/rag/build.py
```

#### 4. 查看切片分析
构建过程中会显示：
- 📊 切片统计信息（数量、大小、分布）
- 🔍 每个切片的详细内容
- ⚠️  潜在问题（过短、重复、特殊字符等）
- 📄 导出完整分析报告到 `knowledge_base/chroma_db/slices_analysis.json`

### Docker 部署

#### 方式 1：直接构建知识库
```bash
# 在项目根目录执行
docker build -t ruralbrain-rag -f src/rag/Dockerfile .

# 运行容器构建知识库
docker run --rm \
  -v $(pwd)/src/data:/app/src/data \
  -v $(pwd)/knowledge_base:/app/knowledge_base \
  ruralbrain-rag
```

#### 方式 2：集成到 docker-compose
```yaml
# 在 docker-compose.yml 中添加
services:
  rag-builder:
    build:
      context: .
      dockerfile: src/rag/Dockerfile
    volumes:
      - ./src/data:/app/src/data
      - ./knowledge_base:/app/knowledge_base
```

## ⚙️ 配置

### 环境变量

创建 `.env` 文件或设置环境变量：

```bash
# 向量数据库类型
VECTOR_DB_TYPE=chroma  # 可选: chroma, faiss, qdrant

# Embedding 模型
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5
EMBEDDING_DEVICE=cpu  # 可选: cuda, mps

# 切片参数（针对 Planning Agent 优化）
CHUNK_SIZE=2500
CHUNK_OVERLAP=500
DEFAULT_TOP_K=5  # 检索返回的切片数量
```

### Python 代码配置

```python
from src.rag.config import (
    CHUNK_SIZE,      # 切片大小（默认 2500）
    CHUNK_OVERLAP,  # 重叠大小（默认 500）
    VECTOR_DB_TYPE,  # 向量数据库类型
)

# 动态修改配置
import os
os.environ["CHUNK_SIZE"] = "3000"  # 更大的切片
```

## 🔧 使用方式

### 在 Agent 中使用

#### 方式 1：标准 Tool 模式
```python
from src.rag.tool import planning_knowledge_tool

# 集成到 LangGraph Agent
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model,
    tools=[planning_knowledge_tool, ...],
    state_modifier="你是一个乡村规划专家，善于利用知识库辅助决策。"
)
```

#### 方式 2：Agentic RAG 模式（推荐）
```python
from src.rag.tool import retrieve_knowledge_detailed

# LLM 自主决定何时检索
@tool(response_format="content_and_artifact")
def search_knowledge(query: str):
    """检索乡村规划相关知识"""
    return retrieve_knowledge_detailed(query)

agent = create_react_agent(
    model,
    tools=[search_knowledge, ...],
)
```

#### 方式 3：直接调用检索函数
```python
from src.rag.tool import retrieve_planning_knowledge

# 检索知识
result = retrieve_planning_knowledge(
    query="博罗古城的发展定位是什么？",
    top_k=5
)
print(result)
```

### 高级用法：元数据过滤
```python
from src.rag.tool import retrieve_with_metadata

# 只检索特定来源的文档
results = retrieve_with_metadata(
    query="发展规划",
    source_filter="luofu_strategy.pptx",
    top_k=3
)
```

## 📊 切片分析工具

### 命令行使用
```python
from src.rag.visualize import SliceInspector
from src.rag.utils import PPTXLoader

# 加载文档
loader = PPTXLoader("path/to/file.pptx")
docs = loader.load()

# 创建检查器
inspector = SliceInspector(docs)

# 打印统计摘要
inspector.print_summary()

# 查看具体切片
inspector.print_slice_details(start_idx=0, end_idx=5)

# 查找问题
inspector.print_issues()

# 导出 JSON
inspector.export_to_json("output.json")
```

### 问题检测

工具会自动检测以下问题：

1. **过短切片**：字符数 < 50
2. **重复内容**：唯一率 < 30%
3. **特殊字符过多**：比例 > 30%
4. **页眉页脚**：包含"第X页"、"机密"等

## 🎯 针对不同场景的优化建议

### 场景 1：宏观战略规划
```python
# 需要大范围上下文
CHUNK_SIZE = 3000
DEFAULT_TOP_K = 10
```

### 场景 2：具体实施建议
```python
# 需要精确的细节信息
CHUNK_SIZE = 1500
DEFAULT_TOP_K = 5
```

### 场景 3：快速问答
```python
# 传统 RAG 模式
CHUNK_SIZE = 500
DEFAULT_TOP_K = 3
```

## 📁 目录结构

```
src/rag/
├── __init__.py
├── config.py              # 配置管理
├── build.py               # 知识库构建脚本
├── tool.py                # LangChain Tool 定义
├── test.py                # 测试脚本
├── Dockerfile             # Docker 部署配置
├── README.md              # 本文档
├── utils/
│   ├── __init__.py
│   └── loaders.py         # 文档加载器
└── visualize/
    ├── __init__.py
    └── inspector.py       # 切片可视化工具

knowledge_base/
└── chroma_db/             # Chroma 向量数据库
    ├── chroma.sqlite3
    └── slices_analysis.json  # 切片分析报告

src/data/
├── luofu_strategy.pptx   # 你的 PPT 文档
└── ...                   # 其他文档
```

## 🔍 故障排查

### 问题 1：找不到知识库
```
FileNotFoundError: 知识库不存在: knowledge_base/chroma_db
```
**解决方案**：先运行 `python src/rag/build.py` 构建知识库

### 问题 2：切片质量差
**解决方案**：
1. 查看切片分析报告：`knowledge_base/chroma_db/slices_analysis.json`
2. 调整 `CHUNK_SIZE` 和 `CHUNK_OVERLAP`
3. 清理源文档中的无用内容

### 问题 3：检索结果不相关
**解决方案**：
1. 增加 `DEFAULT_TOP_K` 获取更多候选
2. 检查 Embedding 模型是否适合你的领域
3. 尝试其他中文 Embedding 模型（如 `BAAI/bge-large-zh-v1.5`）

## 📚 参考资源

- [LangChain RAG 教程](https://python.langchain.com/docs/tutorials/rag/)
- [LangChain Retrievers](https://python.langchain.com/docs/concepts/#retrieval)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [BGE Embedding 模型](https://huggingface.co/BAAI/bge-small-zh-v1.5)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

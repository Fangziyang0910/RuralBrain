# RuralBrain

![LangChain](https://img.shields.io/badge/LangChain-1.0%2B-green?style=flat-square)
![LangGraph](https://img.shields.io/badge/LangGraph-1.0%2B-blue?style=flat-square)
![LangSmith](https://img.shields.io/badge/LangSmith-0.4%2B-orange?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.13%2B-blue?style=flat-square)

## 📋 项目简介

**RuralBrain（乡村智慧大脑）** 是一个复杂的乡村决策系统，利用大语言模型 Agent 技术，为乡村治理和发展提供智能化决策支持。

### 核心能力

- 🔍 **智慧识别**：自动识别和分析乡村发展中的问题与机遇
- 🔬 **自主调研**：基于 Agent 的自主信息收集与分析能力
- 🧠 **复杂决策**：多维度综合评估，提供科学的决策建议

## 🛠️ 技术栈

- **LangChain**: 构建 LLM Agent的核心框架
- **LangGraph**: 实现复杂 Agent 工作流编排
- **LangSmith**: 提供 Agent 行为可观测性和调试能力
- **Python 3.13**: 开发语言

## 🚀 快速开始

### 环境要求

在开始之前，请确保你的系统已安装以下工具：

- **[Python 3.13](https://www.python.org/downloads/)**：项目运行所需的 Python 版本。如果未安装，uv 会自动下载所需版本
- **[uv](https://github.com/astral-sh/uv)**：Python 包管理工具，用于快速安装依赖和管理虚拟环境
- **[Git](https://git-scm.com/downloads)**：版本管理工具，用于克隆和同步代码仓库
- **[WSL](https://learn.microsoft.com/zh-cn/windows/wsl/install)（推荐）**：Windows 用户推荐使用 WSL（Windows Subsystem for Linux）以获得更好的开发体验

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/Fangziyang0910/RuralBrain.git

# 进入项目目录
cd RuralBrain

# 使用 uv 安装依赖并创建虚拟环境
uv sync
```

### 使用 uv 运行代码

```bash
# 运行主程序
uv run main.py

# 或者激活虚拟环境后直接运行
source .venv/bin/activate  # Linux（WSL）/Mac
# .venv\Scripts\activate   # Windows
python main.py
```

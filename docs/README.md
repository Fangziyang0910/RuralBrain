# Docs 目录说明

本目录存放项目开发笔记、设计文档、使用指南等信息，以 Markdown 格式撰写。

## 📁 目录结构

```
docs/
├── README.md                      # 本文件
├── PROJECT_STRUCTURE_GUIDE.md     # 【重要】项目结构组织指南
├── architecture/                  # 架构设计文档
├── guides/                        # 使用指南
├── reports/                       # 测试报告、优化报告
└── api/                           # API 文档
```

## 📖 重要文档

| 文档 | 说明 |
|------|------|
| **[PROJECT_STRUCTURE_GUIDE.md](PROJECT_STRUCTURE_GUIDE.md)** | **必读** - 项目结构组织指南，所有协作者应遵循的规范 |
| [V2 Agent 架构详解.md](V2%20Agent%20架构详解.md) | V2 Agent 架构设计说明 |
| [Agent架构升级方案.md](Agent架构升级方案.md) | Agent 系统升级方案 |
| [model_management.md](model_management.md) | 模型管理指南 |
| [frontend_guide.md](frontend_guide.md) | 前端开发指南 |

## 🛠️ 贡献指南

### 添加新文档时

请遵循以下分类：

- **架构设计** → `docs/architecture/`
- **使用指南** → `docs/guides/`
- **测试报告** → `docs/reports/`
- **API 文档** → `docs/api/`

### 命名规范

- 使用描述性的文件名
- 中文文档可用中文文件名
- 技术文档推荐英文文件名

### 文档模板

```markdown
# 标题

> **版本**: v1.0
> **更新日期**: YYYY-MM-DD
> **作者**: Your Name

## 概述

[简要说明文档目的]

## 内容

[详细内容]

## 更新日志

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|----------|------|
| v1.0 | YYYY-MM-DD | 初始版本 | Your Name |
```

## ⚠️ 注意事项

1. **项目结构规范**: 在添加新文件或目录前，请先阅读 [PROJECT_STRUCTURE_GUIDE.md](PROJECT_STRUCTURE_GUIDE.md)
2. **文档同步**: 代码变更时同步更新相关文档
3. **格式统一**: 使用 Markdown 格式，保持排版整洁
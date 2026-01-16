# RAG 辅助工具脚本

本目录包含用于维护和管理 RAG 知识库的辅助工具脚本。

## 可用脚本

### generate_summaries.py

为现有知识库文档生成摘要（补充阶段2功能）。

**使用场景：**
- 知识库中的文档没有摘要数据
- 重新生成文档摘要
- 批量更新摘要

**使用方法：**
```bash
python src/rag/scripts/generate_summaries.py
```

**功能：**
- 扫描知识库中的所有文档
- 检查每个文档是否已有摘要
- 为没有摘要的文档生成：
  - 执行摘要（200字）
  - 章节摘要（每章300字）
  - 关键要点（10-15条）

**注意：**
- 需要调用 LLM API（DeepSeek 或 GLM）
- 每个文档大约需要 10-15 秒
- 摘要数据会自动保存到 document_index.json

## 未来可能添加的脚本

- `export_summaries.py` - 导出所有摘要到文件
- `update_index.py` - 更新文档索引
- `validate_index.py` - 验证索引完整性
- `merge_docs.py` - 合并多个文档
- `cleanup_cache.py` - 清理向量数据库缓存

## 开发指南

添加新的工具脚本时，请遵循以下规范：

1. **文件命名**：使用动词开头，描述功能（如：`generate_summaries.py`）
2. **函数命名**：使用清晰的动词短语（如：`generate_summaries_for_existing_docs()`）
3. **错误处理**：提供清晰的错误信息
4. **进度提示**：显示处理进度（如：1/10）
5. **确认机制**：危险操作前要求用户确认
6. **文档字符串**：详细说明功能、参数、使用方法

## 相关文件

- 核心模块：`../core/`
- 配置：`../config.py`
- 主要构建脚本：`../build.py`

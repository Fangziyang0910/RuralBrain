"""
工具模块
支持 Markdown、TXT、PPTX、PDF、DOCX、DOC 等多种格式
支持按类别（policies/cases）组织知识库
所有格式统一转换为 Markdown 并自动清理冗余信息
自动检测真实文件类型，不依赖扩展名
"""
from .loaders import (
    MarkdownLoader,
    PPTXLoader,
    TextFileLoader,
    PDFLoader,
    DOCXLoader,
    DOCLoader,
    FileTypeDetector,
    MarkdownCleaner,
    load_documents_from_directory,
    load_knowledge_base,
)

__all__ = [
    "MarkdownLoader",
    "PPTXLoader",
    "TextFileLoader",
    "PDFLoader",
    "DOCXLoader",
    "DOCLoader",
    "FileTypeDetector",
    "MarkdownCleaner",
    "load_documents_from_directory",
    "load_knowledge_base",
]

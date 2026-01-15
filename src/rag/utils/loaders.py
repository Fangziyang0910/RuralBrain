"""
通用文档加载器
支持 Markdown、TXT、PPTX、PDF、DOCX、DOC 等多种格式
符合 LangChain 文档加载器接口规范
支持按类别（policies/cases）组织知识库

所有格式都会统一转换为 Markdown，并自动清理冗余信息
"""
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Literal

from langchain_core.documents import Document
from pptx import Presentation
from pypdf import PdfReader
from docx import Document as DocxDocument
import filetype


# ==================== 文件类型检测工具 ====================

class FileTypeDetector:
    """
    文件类型检测工具
    不依赖扩展名，通过文件内容检测真实类型
    """

    # MIME 类型到文档类型的映射
    MIME_TYPE_MAP = {
        # PDF
        'application/pdf': 'pdf',

        # Word 文档
        'application/msword': 'doc',  # .doc
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/vnd.ms-word': 'doc',
        'application/wps-office.doc': 'doc',  # WPS .doc

        # PowerPoint
        'application/vnd.ms-powerpoint': 'ppt',  # .ppt
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',

        # Excel（用于错误检测）
        'application/vnd.ms-excel': 'xls',  # .xls
        'application/wps-office.xls': 'xls',  # WPS .xls

        # 文本
        'text/plain': 'txt',
        'text/markdown': 'md',

        # OLE 复合文档（老格式）
        'application/x-ole-storage': 'ole',  # 可能是 .doc, .ppt, .xls 等
    }

    @staticmethod
    def detect(file_path: Path) -> str:
        """
        检测文件真实类型

        Args:
            file_path: 文件路径

        Returns:
            文件类型（pdf/doc/docx/ppt/pptx/txt/md）
        """
        ext = file_path.suffix.lower()

        # 先用 filetype 检测
        kind = filetype.guess(str(file_path))

        if kind is None:
            # 无法检测，尝试从扩展名推断
            return FileTypeDetector._ext_to_type(ext)

        # 检查 MIME 类型
        mime_type = kind.mime
        doc_type = FileTypeDetector.MIME_TYPE_MAP.get(mime_type)

        if doc_type:
            # 特殊处理：如果扩展名是 .docx 但检测到的是 OLE 或 Excel 类型，
            # 说明是伪装成 .docx 的 .doc 文件
            if ext == '.docx' and mime_type in [
                'application/vnd.ms-excel',
                'application/wps-office.xls',
                'application/x-ole-storage'
            ]:
                print(f"⚠️  检测到伪装成 .docx 的 .doc 文件: {file_path.name}")
                return 'doc'

            return doc_type

        # 特殊处理：如果检测到 OLE 复合文档，根据扩展名判断
        if mime_type == 'application/x-ole-storage':
            if ext in ['.doc', '.ppt', '.xls']:
                return ext[1:]  # 去掉点号

        # 无法识别，回退到扩展名
        return FileTypeDetector._ext_to_type(ext)

    @staticmethod
    def _ext_to_type(ext: str) -> str:
        """扩展名到类型映射"""
        ext_map = {
            '.pdf': 'pdf',
            '.doc': 'doc',
            '.docx': 'docx',
            '.ppt': 'ppt',
            '.pptx': 'pptx',
            '.txt': 'txt',
            '.md': 'markdown',
        }
        return ext_map.get(ext.lower(), 'unknown')


# ==================== Markdown 清理工具 ====================

class MarkdownCleaner:
    """
    Markdown 内容清理工具
    去除格式数据、冗余信息、空白过多等垃圾内容
    """

    # 需要过滤的页眉页脚模式
    FOOTER_PATTERNS = [
        r'第\s*\d+\s*页',
        r'Page\s*\d+',
        r'保密|机密|内部资料',
        r'www\.\w+\.com',
        r'http[s]?://\S+',
    ]

    # 需要过滤的模板占位符
    PLACEHOLDER_PATTERNS = [
        r'点击此处添加.*',
        r'请输入.*',
        r'\[.*?\]',  # 方括号中的占位符
        r'{{.*?}}',  # 双花括号中的占位符
    ]

    @staticmethod
    def clean_text(text: str) -> str:
        """
        清理文本内容

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 1. 去除页眉页脚
        for pattern in MarkdownCleaner.FOOTER_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # 2. 去除模板占位符
        for pattern in MarkdownCleaner.PLACEHOLDER_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # 3. 去除过多的空白行（保留最多 2 个连续空行）
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n\n', text)

        # 4. 去除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        # 5. 去除特殊字符过多但内容很少的行
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # 统计中文字符和字母数字
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', line))
            alnum_chars = len(re.findall(r'[a-zA-Z0-9]', line))
            total_chars = len(line)

            # 如果有效字符占比超过 10% 或绝对数量超过 5，则保留
            if (chinese_chars + alnum_chars) / max(total_chars, 1) > 0.1 or (chinese_chars + alnum_chars) >= 5:
                cleaned_lines.append(line)

        text = '\n'.join(cleaned_lines)

        # 6. 去除首尾空白
        text = text.strip()

        return text

    @staticmethod
    def is_meaningful_content(text: str, min_length: int = 20) -> bool:
        """
        判断文本是否有意义

        Args:
            text: 文本内容
            min_length: 最小长度阈值

        Returns:
            是否有意义
        """
        # 过滤太短的文本
        if len(text.strip()) < min_length:
            return False

        # 过滤只有符号的文本
        if not re.search(r'[\u4e00-\u9fff\u4e00-\u9fa5a-zA-Z0-9]', text):
            return False

        # 过滤纯数字或日期
        if text.strip().replace('-', '').replace('/', '').replace(':', '').strip().isdigit():
            return False

        return True


# ==================== DOC 加载器（Legacy Word 格式）====================

class DOCLoader:
    """
    Word 文档加载器（DOC - Legacy Office 97-2003 格式）
    使用 antiword 或 catdoc 命令行工具提取文本
    """

    def __init__(
        self,
        file_path: str | Path,
        category: Optional[Literal["policies", "cases"]] = None,
    ):
        self.file_path = Path(file_path)
        self.category = category
        self.cleaner = MarkdownCleaner()

    def _extract_with_antiword(self) -> str:
        """使用 antiword 提取文本"""
        try:
            result = subprocess.run(
                ['antiword', str(self.file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout
            raise Exception(f"antiword failed with code {result.returncode}")
        except FileNotFoundError:
            raise Exception("antiword 未安装，请运行: sudo apt-get install antiword")
        except subprocess.TimeoutExpired:
            raise Exception("文档提取超时")

    def _extract_with_catdoc(self) -> str:
        """使用 catdoc 提取文本"""
        try:
            result = subprocess.run(
                ['catdoc', str(self.file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout
            raise Exception(f"catdoc failed with code {result.returncode}")
        except FileNotFoundError:
            raise Exception("catdoc 未安装，请运行: sudo apt-get install catdoc")
        except subprocess.TimeoutExpired:
            raise Exception("文档提取超时")

    def load(self) -> List[Document]:
        """加载 DOC 文件并返回文档列表"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"找不到文件: {self.file_path}")

        print(f"📝 正在读取 Word 文档（DOC 格式）: {self.file_path} ...")

        try:
            # 尝试使用 antiword（推荐）
            try:
                text = self._extract_with_antiword()
            except Exception as e:
                print(f"⚠️  antiword 失败，尝试 catdoc: {e}")
                text = self._extract_with_catdoc()

            # 清理文本
            cleaned_text = self.cleaner.clean_text(text)

            # 按段落分割
            paragraphs = [p.strip() for p in cleaned_text.split('\n\n') if p.strip()]

            documents = []
            for idx, paragraph in enumerate(paragraphs, start=1):
                if self.cleaner.is_meaningful_content(paragraph):
                    # 转换为 Markdown 格式
                    md_content = f"## 段落 {idx}\n\n{paragraph}"

                    metadata = {
                        "source": str(self.file_path.name),
                        "paragraph": idx,
                        "type": "doc",
                    }

                    if self.category:
                        metadata["category"] = self.category

                    doc = Document(page_content=md_content, metadata=metadata)
                    documents.append(doc)

            print(f"✅ 提取完成，共获取 {len(documents)} 个段落")
            return documents

        except Exception as e:
            raise Exception(f"读取 Word 文档（DOC）失败: {e}\n提示: 请安装 antiword: sudo apt-get install antiword")


# ==================== DOCX 加载器（已优化）====================

class DOCXLoader:
    """
    Word 文档加载器（DOCX）
    提取文本内容并转换为 Markdown 格式，保留标题层级结构
    """

    def __init__(
        self,
        file_path: str | Path,
        category: Optional[Literal["policies", "cases"]] = None,
    ):
        self.file_path = Path(file_path)
        self.category = category
        self.cleaner = MarkdownCleaner()

    def load(self) -> List[Document]:
        """加载 DOCX 文件并返回文档列表"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"找不到文件: {self.file_path}")

        print(f"📝 正在读取 Word 文档（DOCX 格式）: {self.file_path} ...")

        try:
            doc = DocxDocument(str(self.file_path))
            documents = []

            # 按段落提取内容
            current_content = []
            current_heading = "文档开始"
            current_level = 0
            paragraph_count = 0

            for para in doc.paragraphs:
                text = para.text.strip()

                if not text:
                    continue

                # 检测标题（Word 内置样式）
                style_name = para.style.name if para.style else ""

                if 'Heading' in style_name:
                    # 保存之前的内容
                    if current_content:
                        content = '\n'.join(current_content).strip()
                        cleaned_content = self.cleaner.clean_text(content)

                        if self.cleaner.is_meaningful_content(cleaned_content):
                            md_content = f"{'#' * current_level} {current_heading}\n\n{cleaned_content}"

                            metadata = {
                                "source": str(self.file_path.name),
                                "paragraph": paragraph_count,
                                "type": "docx",
                            }

                            if self.category:
                                metadata["category"] = self.category

                            doc = Document(page_content=md_content, metadata=metadata)
                            documents.append(doc)

                    # 开始新标题
                    current_content = []
                    current_heading = text

                    # 提取标题级别（Heading 1 -> #, Heading 2 -> ##, etc.）
                    if 'Heading 1' in style_name:
                        current_level = 1
                    elif 'Heading 2' in style_name:
                        current_level = 2
                    elif 'Heading 3' in style_name:
                        current_level = 3
                    elif 'Heading 4' in style_name:
                        current_level = 4
                    elif 'Heading 5' in style_name:
                        current_level = 5
                    else:
                        current_level = 6

                    paragraph_count += 1

                else:
                    # 普通段落
                    current_content.append(text)

            # 保存最后的内容
            if current_content:
                content = '\n'.join(current_content).strip()
                cleaned_content = self.cleaner.clean_text(content)

                if self.cleaner.is_meaningful_content(cleaned_content):
                    md_content = f"{'#' * current_level} {current_heading}\n\n{cleaned_content}"

                    metadata = {
                        "source": str(self.file_path.name),
                        "paragraph": paragraph_count,
                        "type": "docx",
                    }

                    if self.category:
                        metadata["category"] = self.category

                    doc = Document(page_content=md_content, metadata=metadata)
                    documents.append(doc)

            # 如果没有检测到标题，按段落切分
            if not documents:
                paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

                for idx, para_text in enumerate(paragraphs, start=1):
                    cleaned_text = self.cleaner.clean_text(para_text)

                    if self.cleaner.is_meaningful_content(cleaned_text):
                        md_content = f"## 段落 {idx}\n\n{cleaned_text}"

                        metadata = {
                            "source": str(self.file_path.name),
                            "paragraph": idx,
                            "type": "docx",
                        }

                        if self.category:
                            metadata["category"] = self.category

                        doc = Document(page_content=md_content, metadata=metadata)
                        documents.append(doc)

            print(f"✅ 提取完成，共获取 {len(documents)} 个文档片段")
            return documents

        except Exception as e:
            # 如果 python-docx 失败，尝试降级到 DOCLoader
            print(f"⚠️  python-docx 读取失败: {e}")
            print(f"⚠️  可能是伪装成 .docx 的 .doc 文件，尝试使用 DOCLoader...")
            doc_loader = DOCLoader(self.file_path, self.category)
            return doc_loader.load()


# ==================== PDF 加载器 ====================

class PDFLoader:
    """
    PDF 文档加载器
    提取文本内容并转换为 Markdown 格式
    """

    def __init__(
        self,
        file_path: str | Path,
        category: Optional[Literal["policies", "cases"]] = None,
    ):
        self.file_path = Path(file_path)
        self.category = category
        self.cleaner = MarkdownCleaner()

    def load(self) -> List[Document]:
        """加载 PDF 文件并返回文档列表"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"找不到文件: {self.file_path}")

        print(f"📄 正在读取 PDF: {self.file_path} ...")

        try:
            reader = PdfReader(str(self.file_path))
            documents = []

            # 按页提取文本
            for page_idx, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text()

                    if not text or not text.strip():
                        continue

                    # 清理文本
                    cleaned_text = self.cleaner.clean_text(text)

                    # 检查是否有意义
                    if not self.cleaner.is_meaningful_content(cleaned_text):
                        continue

                    # 转换为 Markdown 格式
                    md_content = f"# 第 {page_idx} 页\n\n{cleaned_text}"

                    # 构造元数据
                    metadata = {
                        "source": str(self.file_path.name),
                        "page": page_idx,
                        "type": "pdf",
                    }

                    if self.category:
                        metadata["category"] = self.category

                    doc = Document(page_content=md_content, metadata=metadata)
                    documents.append(doc)

                except Exception as e:
                    print(f"⚠️  处理第 {page_idx} 页时出错: {e}")
                    continue

            print(f"✅ 提取完成，共获取 {len(documents)} 页有效内容")
            return documents

        except Exception as e:
            raise Exception(f"读取 PDF 文件失败: {e}")


# ==================== PPTX 加载器（已优化）====================

class PPTXLoader:
    """
    PPTX 文档加载器
    提取文本内容并转换为 Markdown 格式
    """

    def __init__(
        self,
        file_path: str | Path,
        category: Optional[Literal["policies", "cases"]] = None,
    ):
        self.file_path = Path(file_path)
        self.category = category
        self.cleaner = MarkdownCleaner()

    def load(self) -> List[Document]:
        """加载 PPTX 文件并返回文档列表"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"找不到文件: {self.file_path}")

        print(f"📂 正在读取 PPT: {self.file_path} ...")
        prs = Presentation(str(self.file_path))
        documents = []

        for slide_idx, slide in enumerate(prs.slides, start=1):
            slide_texts = []

            # 提取文本框内容
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text = shape.text.strip()
                    slide_texts.append(text)

            # 合并并清理文本
            if slide_texts:
                content = "\n".join(slide_texts)
                cleaned_content = self.cleaner.clean_text(content)

                if self.cleaner.is_meaningful_content(cleaned_content):
                    # 转换为 Markdown 格式
                    md_content = f"# 第 {slide_idx} 页\n\n{cleaned_content}"

                    # 构造元数据
                    metadata = {
                        "source": str(self.file_path.name),
                        "page": slide_idx,
                        "type": "pptx",
                    }

                    if self.category:
                        metadata["category"] = self.category

                    doc = Document(page_content=md_content, metadata=metadata)
                    documents.append(doc)

        print(f"✅ 提取完成，共获取 {len(documents)} 页有效内容")
        return documents


# ==================== Markdown 加载器（保持不变）====================

class MarkdownLoader:
    """
    Markdown 文档加载器
    按标题层级分割 Markdown 文件，保留结构化信息
    """

    def __init__(
        self,
        file_path: str | Path,
        encoding: str = "utf-8",
        category: Optional[Literal["policies", "cases"]] = None,
    ):
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.category = category
        self.cleaner = MarkdownCleaner()

    def load(self) -> List[Document]:
        """加载 Markdown 文件并返回文档列表"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"找不到文件: {self.file_path}")

        print(f"📄 正在读取 Markdown: {self.file_path} ...")
        with open(self.file_path, "r", encoding=self.encoding, errors="ignore") as f:
            content = f.read()

        # 清理内容
        content = self.cleaner.clean_text(content)

        # 按标题分割（支持 # ## ### 等）
        documents = self._split_by_headers(content)

        print(f"✅ 提取完成，共获取 {len(documents)} 个文档片段")
        return documents

    def _split_by_headers(self, content: str) -> List[Document]:
        """
        按 Markdown 标题分割文档
        保留标题层级和结构
        """
        documents = []

        # 按行分割
        lines = content.split("\n")

        current_section = []
        current_header = "文档开始"
        current_level = 0
        section_idx = 0

        for line in lines:
            # 检测标题（# ## ### 等）
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if header_match:
                # 保存之前的章节
                if current_section:
                    section_content = "\n".join(current_section).strip()

                    if self.cleaner.is_meaningful_content(section_content):
                        metadata = self._build_metadata(
                            current_header, current_level, section_idx
                        )
                        doc = Document(page_content=section_content, metadata=metadata)
                        documents.append(doc)
                        section_idx += 1

                # 开始新章节
                current_level = len(header_match.group(1))
                current_header = header_match.group(2).strip()
                current_section = [line]  # 标题行也包含在内容中
            else:
                current_section.append(line)

        # 保存最后一个章节
        if current_section:
            section_content = "\n".join(current_section).strip()
            if self.cleaner.is_meaningful_content(section_content):
                metadata = self._build_metadata(
                    current_header, current_level, section_idx
                )
                doc = Document(page_content=section_content, metadata=metadata)
                documents.append(doc)

        return documents

    def _build_metadata(
        self, header: str, level: int, section_idx: int
    ) -> Dict[str, any]:
        """构建文档元数据"""
        metadata = {
            "source": str(self.file_path.name),
            "section": section_idx + 1,
            "type": "markdown",
            "header": header,
            "header_level": level,
        }

        # 如果指定了类别，添加到元数据
        if self.category:
            metadata["category"] = self.category

        return metadata


# ==================== 文本文件加载器（已优化）====================

class TextFileLoader:
    """
    TXT 文档加载器
    按段落分割文本文件，转换为 Markdown 格式
    """

    def __init__(
        self,
        file_path: str | Path,
        encoding: str = "utf-8",
        category: Optional[Literal["policies", "cases"]] = None,
    ):
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.category = category
        self.cleaner = MarkdownCleaner()

    def load(self) -> List[Document]:
        """加载文本文件并返回文档列表"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"找不到文件: {self.file_path}")

        print(f"📂 正在读取文本文件: {self.file_path} ...")
        with open(self.file_path, "r", encoding=self.encoding, errors="ignore") as f:
            content = f.read()

        # 清理文本
        content = self.cleaner.clean_text(content)

        # 按段落分割
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        documents = []
        for idx, paragraph in enumerate(paragraphs, start=1):
            if self.cleaner.is_meaningful_content(paragraph):
                # 转换为 Markdown 格式
                md_content = f"## 段落 {idx}\n\n{paragraph}"

                metadata = {
                    "source": str(self.file_path.name),
                    "paragraph": idx,
                    "type": "text",
                }

                # 如果指定了类别，添加到元数据
                if self.category:
                    metadata["category"] = self.category

                doc = Document(page_content=md_content, metadata=metadata)
                documents.append(doc)

        print(f"✅ 提取完成，共获取 {len(documents)} 个段落")
        return documents


# ==================== 批量加载函数（已优化）====================

def load_documents_from_directory(
    directory: str | Path,
    file_extensions: Optional[List[str]] = None,
    category: Optional[Literal["policies", "cases"]] = None,
) -> List[Document]:
    """
    从目录批量加载文档
    自动检测真实文件类型，不依赖扩展名

    Args:
        directory: 文档目录路径
        file_extensions: 要加载的文件扩展名列表，如 [".md", ".txt", ".pptx", ".pdf", ".docx", ".doc"]
        category: 文档类别（"policies" 或 "cases"），会添加到元数据中

    Returns:
        所有文档的列表
    """
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"目录不存在: {directory}")

    if file_extensions is None:
        file_extensions = [".md", ".txt", ".pptx", ".ppt", ".pdf", ".docx", ".doc"]

    all_documents = []

    # 遍历目录下的所有文件
    for file_path in directory.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in file_extensions:
            try:
                # 检测真实文件类型
                real_type = FileTypeDetector.detect(file_path)

                print(f"🔍 检测文件类型: {file_path.name} -> {real_type}")

                # 根据真实类型选择加载器
                if real_type == 'pdf':
                    loader = PDFLoader(file_path, category=category)
                elif real_type == 'doc':
                    loader = DOCLoader(file_path, category=category)
                elif real_type == 'docx':
                    loader = DOCXLoader(file_path, category=category)
                elif real_type == 'ppt':
                    print(f"⚠️  暂不支持 PPT 格式，请转换为 PPTX: {file_path.name}")
                    continue
                elif real_type == 'pptx':
                    loader = PPTXLoader(file_path, category=category)
                elif real_type == 'markdown':
                    loader = MarkdownLoader(file_path, category=category)
                elif real_type == 'txt':
                    loader = TextFileLoader(file_path, category=category)
                else:
                    print(f"⚠️  不支持的文件类型: {real_type}，跳过: {file_path.name}")
                    continue

                documents = loader.load()
                all_documents.extend(documents)

            except Exception as e:
                print(f"⚠️  加载文件 {file_path} 时出错: {e}")
                continue

    print(f"📚 总共加载了 {len(all_documents)} 个文档片段")
    return all_documents


def load_knowledge_base(
    data_dir: str | Path,
    categories: Optional[List[Literal["policies", "cases"]]] = None,
) -> List[Document]:
    """
    加载知识库（支持分类）
    自动检测真实文件类型，不依赖扩展名

    目录结构:
    data/
    ├── policies/
    │   ├── 文件1.md
    │   └── 文件2.pdf（可能是 .doc 伪装的）
    └── cases/
        ├── 案例1.docx
        └── 案例2.pptx

    Args:
        data_dir: 数据根目录（默认为 src/data）
        categories: 要加载的类别列表，如 ["policies", "cases"]。
                     如果为 None，则加载所有类别。

    Returns:
        所有文档的列表
    """
    data_dir = Path(data_dir)

    if categories is None:
        # 自动检测所有子目录作为类别
        categories = []
        for item in data_dir.iterdir():
            if item.is_dir() and item.name in ["policies", "cases"]:
                categories.append(item.name)

    if not categories:
        raise FileNotFoundError(
            f"未找到任何类别目录。请在 {data_dir} 下创建 'policies' 和/或 'cases' 目录。"
        )

    all_documents = []

    for category in categories:
        category_dir = data_dir / category

        if not category_dir.exists():
            print(f"⚠️  目录不存在，跳过: {category_dir}")
            continue

        print(f"\n{'='*60}")
        print(f"正在加载类别: {category}")
        print(f"{'='*60}")

        documents = load_documents_from_directory(
            category_dir,
            file_extensions=[".md", ".txt", ".pptx", ".ppt", ".pdf", ".docx", ".doc"],
            category=category,  # 添加类别标记到元数据
        )

        all_documents.extend(documents)

    print(f"\n{'='*60}")
    print(f"✅ 知识库加载完成！")
    print(f"   - 总文档数: {len(all_documents)}")
    print(f"   - 类别: {', '.join(categories)}")
    print(f"{'='*60}\n")

    return all_documents

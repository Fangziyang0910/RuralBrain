"""
通用文档加载器

支持 Markdown、TXT、PPTX、PDF、DOCX、DOC 等多种格式。
符合 LangChain 文档加载器接口规范，支持按类别（policies/cases）组织知识库。
所有格式都会统一转换为 Markdown，并自动清理冗余信息。
"""
import re
import subprocess
from pathlib import Path
from typing import Optional, Literal

from langchain_core.documents import Document
import filetype

# Optional imports for specific file formats
try:
    from pptx import Presentation
except ImportError:
    Presentation = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None


# ==================== 文件类型检测 ====================

class FileTypeDetector:
    """通过文件内容检测真实类型，不依赖扩展名"""

    MIME_TYPE_MAP = {
        'application/pdf': 'pdf',
        'application/msword': 'doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/vnd.ms-word': 'doc',
        'application/wps-office.doc': 'doc',
        'application/vnd.ms-powerpoint': 'ppt',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
        'application/vnd.ms-excel': 'xls',
        'application/wps-office.xls': 'xls',
        'text/plain': 'txt',
        'text/markdown': 'md',
        'application/x-ole-storage': 'ole',
    }

    EXT_TYPE_MAP = {
        '.pdf': 'pdf', '.doc': 'doc', '.docx': 'docx',
        '.ppt': 'ppt', '.pptx': 'pptx', '.txt': 'txt',
        '.md': 'markdown',
    }

    @classmethod
    def detect(cls, file_path: Path) -> str:
        """检测文件真实类型"""
        ext = file_path.suffix.lower()
        kind = filetype.guess(str(file_path))

        if kind is None:
            return cls.EXT_TYPE_MAP.get(ext, 'unknown')

        mime_type = kind.mime
        doc_type = cls.MIME_TYPE_MAP.get(mime_type)

        if doc_type == 'ole':
            return 'doc' if ext in ['.doc', '.docx'] else doc_type

        if ext == '.docx' and mime_type in [
            'application/vnd.ms-excel',
            'application/wps-office.xls',
            'application/x-ole-storage'
        ]:
            print(f"⚠️  检测到伪装成 .docx 的 .doc 文件: {file_path.name}")
            return 'doc'

        return doc_type or cls.EXT_TYPE_MAP.get(ext, 'unknown')


# ==================== Markdown 清理 ====================

class MarkdownCleaner:
    """清理 Markdown 内容，去除格式数据和冗余信息"""

    FOOTER_PATTERNS = [
        r'第\s*\d+\s*页', r'Page\s*\d+',
        r'保密|机密|内部资料', r'www\.\w+\.com', r'http[s]?://\S+',
    ]

    PLACEHOLDER_PATTERNS = [
        r'点击此处添加.*', r'请输入.*', r'\[.*?\]', r'{{.*?}}',
    ]

    @classmethod
    def clean_text(cls, text: str) -> str:
        """清理文本内容"""
        for pattern in cls.FOOTER_PATTERNS + cls.PLACEHOLDER_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        text = re.sub(r'\n\s*\n\s*\n+', '\n\n\n', text)
        lines = [line.strip() for line in text.split('\n')]

        cleaned_lines = []
        for line in lines:
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', line))
            alnum_chars = len(re.findall(r'[a-zA-Z0-9]', line))
            total_chars = len(line)

            if (chinese_chars + alnum_chars) / max(total_chars, 1) > 0.1 or (chinese_chars + alnum_chars) >= 5:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

    @classmethod
    def is_meaningful_content(cls, text: str, min_length: int = 20) -> bool:
        """判断文本是否有意义"""
        if len(text.strip()) < min_length:
            return False
        if not re.search(r'[\u4e00-\u9fff\u4e00-\u9fa5a-zA-Z0-9]', text):
            return False
        if text.strip().replace('-', '').replace('/', '').replace(':', '').strip().isdigit():
            return False
        return True


# ==================== 基础加载器 ====================

class BaseDocumentLoader:
    """文档加载器基类，提供公共方法"""

    def __init__(
        self,
        file_path: str | Path,
        category: Optional[Literal["policies", "cases"]] = None,
    ):
        self.file_path = Path(file_path)
        self.category = category
        self.cleaner = MarkdownCleaner()

    def _create_document(
        self,
        content: str,
        **metadata_kwargs
    ) -> Optional[Document]:
        """创建文档对象"""
        if not self.cleaner.is_meaningful_content(content):
            return None

        cleaned_content = self.cleaner.clean_text(content)
        if not self.cleaner.is_meaningful_content(cleaned_content):
            return None

        metadata = {
            "source": str(self.file_path.name),
            **metadata_kwargs
        }

        if self.category:
            metadata["category"] = self.category

        return Document(page_content=cleaned_content, metadata=metadata)

    def _validate_file(self) -> None:
        """验证文件存在"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"找不到文件: {self.file_path}")


# ==================== DOC 加载器 ====================

class DOCLoader(BaseDocumentLoader):
    """Word 文档加载器（DOC - Legacy Office 97-2003 格式）"""

    def load(self) -> list[Document]:
        """加载 DOC 文件"""
        self._validate_file()
        print(f"📝 正在读取 Word 文档（DOC 格式）: {self.file_path} ...")

        try:
            text = self._extract_text()
            return self._parse_text(text)
        except Exception as e:
            raise Exception(f"读取 Word 文档（DOC）失败: {e}\n提示: 请安装 catdoc: sudo apt-get install catdoc")

    def _extract_text(self) -> str:
        """尝试多种方法提取文本"""
        extractors = [
            self._extract_with_antiword,
            self._extract_with_catdoc,
            self._extract_with_olefile,
        ]

        for idx, extractor in enumerate(extractors, 1):
            try:
                if idx > 1:
                    print(f"⚠️  前一种方法失败，尝试下一种...")
                return extractor()
            except Exception as e:
                continue

        raise Exception("所有提取方法都失败")

    def _extract_with_antiword(self) -> str:
        """使用 antiword 提取文本"""
        try:
            result = subprocess.run(
                ['antiword', str(self.file_path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout
            raise Exception(f"antiword failed with code {result.returncode}")
        except FileNotFoundError:
            raise Exception("antiword 未安装，请运行: sudo apt-get install antiword")

    def _extract_with_catdoc(self) -> str:
        """使用 catdoc 提取文本"""
        try:
            result = subprocess.run(
                ['catdoc', str(self.file_path)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout
            raise Exception(f"catdoc failed with code {result.returncode}")
        except FileNotFoundError:
            raise Exception("catdoc 未安装，请运行: sudo apt-get install catdoc")

    def _extract_with_olefile(self) -> str:
        """使用 olefile 提取文本（纯 Python 备用方案）"""
        try:
            import olefile
        except ImportError:
            raise Exception("olefile 未安装，请运行: uv add olefile")

        ole = olefile.OleFileIO(self.file_path)

        if not ole.exists('WordDocument'):
            raise Exception("不是有效的 Word 文档")

        text_parts = []
        streams_to_try = ['WordDocument', '1Table', '0Table', 'Data']

        for stream_name in streams_to_try:
            if not ole.exists(stream_name):
                continue

            try:
                data = ole.openstream(stream_name).read()
                print(f"   正在解析流: {stream_name} ({len(data)} 字节)")

                for encoding in ['utf-16le', 'utf-16be', 'gbk', 'gb2312', 'gb18030', 'utf-8']:
                    try:
                        decoded = data.decode(encoding, errors='ignore')
                        chinese_chars = re.findall(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+', decoded)
                        if chinese_chars:
                            text_segment = ''.join(chinese_chars)
                            text_segment = re.sub(r'\s+', '\n', text_segment)
                            text_segment = re.sub(r'\n{3,}', '\n\n', text_segment)

                            if len(text_segment.strip()) > 20:
                                print(f"   ✓ 使用 {encoding} 编码提取了 {len(text_segment)} 个字符")
                                text_parts.append(text_segment)
                                break
                    except:
                        continue
            except Exception as e:
                print(f"   ⚠️  解析流 {stream_name} 失败: {e}")
                continue

        ole.close()

        if not text_parts:
            raise Exception("未能从文档中提取到有效文本，请将文件转换为 .docx 格式")

        return '\n\n'.join(text_parts)

    def _parse_text(self, text: str) -> list[Document]:
        """解析提取的文本"""
        cleaned_text = self.cleaner.clean_text(text)
        paragraphs = [p.strip() for p in cleaned_text.split('\n\n') if p.strip()]

        documents = []
        for idx, paragraph in enumerate(paragraphs, start=1):
            doc = self._create_document(
                f"## 段落 {idx}\n\n{paragraph}",
                paragraph=idx,
                type="doc",
            )
            if doc:
                documents.append(doc)

        print(f"✅ 提取完成，共获取 {len(documents)} 个段落")
        return documents


# ==================== DOCX 加载器 ====================

class DOCXLoader(BaseDocumentLoader):
    """Word 文档加载器（DOCX）"""

    def load(self) -> list[Document]:
        """加载 DOCX 文件"""
        self._validate_file()
        print(f"📝 正在读取 Word 文档（DOCX 格式）: {self.file_path} ...")

        if DocxDocument is None:
            raise Exception("python-docx 未安装，请运行: uv add python-docx")

        try:
            doc = DocxDocument(str(self.file_path))
            return self._parse_docx(doc)
        except Exception as e:
            print(f"⚠️  python-docx 读取失败: {e}")
            print(f"⚠️  可能是伪装成 .docx 的 .doc 文件，尝试使用 DOCLoader...")
            return DOCLoader(self.file_path, self.category).load()

    def _parse_docx(self, doc) -> list[Document]:
        """解析 DOCX 文档"""
        documents = []
        current_content = []
        current_heading = "文档开始"
        current_level = 0
        paragraph_count = 0

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            style_name = para.style.name if para.style else ""

            if 'Heading' in style_name:
                if current_content:
                    doc = self._create_document(
                        '\n'.join(current_content).strip(),
                        paragraph=paragraph_count,
                        type="docx",
                    )
                    if doc:
                        documents.append(doc)

                current_content = []
                current_heading = text
                current_level = self._extract_heading_level(style_name)
                paragraph_count += 1
            else:
                current_content.append(text)

        if current_content:
            doc = self._create_document(
                '\n'.join(current_content).strip(),
                paragraph=paragraph_count,
                type="docx",
            )
            if doc:
                documents.append(doc)

        if not documents:
            return self._parse_as_paragraphs(doc)

        print(f"✅ 提取完成，共获取 {len(documents)} 个文档片段")
        return documents

    def _extract_heading_level(self, style_name: str) -> int:
        """从样式名称提取标题级别"""
        for i in range(1, 7):
            if f'Heading {i}' in style_name:
                return i
        return 6

    def _parse_as_paragraphs(self, doc) -> list[Document]:
        """按段落解析（当没有检测到标题时）"""
        documents = []
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

        for idx, para_text in enumerate(paragraphs, start=1):
            doc = self._create_document(
                f"## 段落 {idx}\n\n{para_text}",
                paragraph=idx,
                type="docx",
            )
            if doc:
                documents.append(doc)

        return documents


# ==================== PDF 加载器 ====================

class PDFLoader(BaseDocumentLoader):
    """PDF 文档加载器"""

    def load(self) -> list[Document]:
        """加载 PDF 文件"""
        self._validate_file()
        print(f"📄 正在读取 PDF: {self.file_path} ...")

        if PdfReader is None:
            raise Exception("pypdf 未安装，请运行: uv add pypdf")

        try:
            reader = PdfReader(str(self.file_path))
            return self._parse_pdf(reader)
        except Exception as e:
            raise Exception(f"读取 PDF 文件失败: {e}")

    def _parse_pdf(self, reader) -> list[Document]:
        """解析 PDF 文档"""
        documents = []

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text()
                if not text or not text.strip():
                    continue

                doc = self._create_document(
                    f"# 第 {page_idx} 页\n\n{text}",
                    page=page_idx,
                    type="pdf",
                )
                if doc:
                    documents.append(doc)
            except Exception as e:
                print(f"⚠️  处理第 {page_idx} 页时出错: {e}")
                continue

        print(f"✅ 提取完成，共获取 {len(documents)} 页有效内容")
        return documents


# ==================== PPTX 加载器 ====================

class PPTXLoader(BaseDocumentLoader):
    """PPTX 文档加载器"""

    def load(self) -> list[Document]:
        """加载 PPTX 文件"""
        self._validate_file()
        print(f"📂 正在读取 PPT: {self.file_path} ...")

        if Presentation is None:
            raise Exception("python-pptx 未安装，请运行: uv add python-pptx")

        prs = Presentation(str(self.file_path))
        documents = []

        for slide_idx, slide in enumerate(prs.slides, start=1):
            slide_texts = [
                shape.text.strip()
                for shape in slide.shapes
                if hasattr(shape, "text") and shape.text.strip()
            ]

            if slide_texts:
                content = "\n".join(slide_texts)
                doc = self._create_document(
                    f"# 第 {slide_idx} 页\n\n{content}",
                    page=slide_idx,
                    type="pptx",
                )
                if doc:
                    documents.append(doc)

        print(f"✅ 提取完成，共获取 {len(documents)} 页有效内容")
        return documents


# ==================== Markdown 加载器 ====================

class MarkdownLoader(BaseDocumentLoader):
    """Markdown 文档加载器"""

    def __init__(
        self,
        file_path: str | Path,
        encoding: str = "utf-8",
        category: Optional[Literal["policies", "cases"]] = None,
    ):
        super().__init__(file_path, category)
        self.encoding = encoding

    def load(self) -> list[Document]:
        """加载 Markdown 文件"""
        self._validate_file()
        print(f"📄 正在读取 Markdown: {self.file_path} ...")

        with open(self.file_path, "r", encoding=self.encoding, errors="ignore") as f:
            content = f.read()

        content = self.cleaner.clean_text(content)
        documents = self._split_by_headers(content)

        print(f"✅ 提取完成，共获取 {len(documents)} 个文档片段")
        return documents

    def _split_by_headers(self, content: str) -> list[Document]:
        """按 Markdown 标题分割文档"""
        documents = []
        lines = content.split("\n")

        current_section = []
        current_header = "文档开始"
        current_level = 0
        section_idx = 0

        for line in lines:
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if header_match:
                if current_section:
                    section_content = "\n".join(current_section).strip()
                    doc = self._create_document(
                        section_content,
                        section=section_idx + 1,
                        type="markdown",
                        header=current_header,
                        header_level=current_level,
                    )
                    if doc:
                        documents.append(doc)
                        section_idx += 1

                current_level = len(header_match.group(1))
                current_header = header_match.group(2).strip()
                current_section = [line]
            else:
                current_section.append(line)

        if current_section:
            section_content = "\n".join(current_section).strip()
            doc = self._create_document(
                section_content,
                section=section_idx + 1,
                type="markdown",
                header=current_header,
                header_level=current_level,
            )
            if doc:
                documents.append(doc)

        return documents


# ==================== 文本文件加载器 ====================

class TextFileLoader(BaseDocumentLoader):
    """TXT 文档加载器"""

    def __init__(
        self,
        file_path: str | Path,
        encoding: str = "utf-8",
        category: Optional[Literal["policies", "cases"]] = None,
    ):
        super().__init__(file_path, category)
        self.encoding = encoding

    def load(self) -> list[Document]:
        """加载文本文件"""
        self._validate_file()
        print(f"📂 正在读取文本文件: {self.file_path} ...")

        with open(self.file_path, "r", encoding=self.encoding, errors="ignore") as f:
            content = f.read()

        content = self.cleaner.clean_text(content)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        documents = []
        for idx, paragraph in enumerate(paragraphs, start=1):
            doc = self._create_document(
                f"## 段落 {idx}\n\n{paragraph}",
                paragraph=idx,
                type="text",
            )
            if doc:
                documents.append(doc)

        print(f"✅ 提取完成，共获取 {len(documents)} 个段落")
        return documents


# ==================== 批量加载函数 ====================

def load_documents_from_directory(
    directory: str | Path,
    file_extensions: Optional[list[str]] = None,
    category: Optional[Literal["policies", "cases"]] = None,
) -> list[Document]:
    """从目录批量加载文档，自动检测真实文件类型"""
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"目录不存在: {directory}")

    if file_extensions is None:
        file_extensions = [".md", ".txt", ".pptx", ".ppt", ".pdf", ".docx", ".doc"]

    all_documents = []

    for file_path in directory.rglob("*"):
        if not file_path.is_file() or file_path.suffix.lower() not in file_extensions:
            continue

        try:
            real_type = FileTypeDetector.detect(file_path)
            print(f"🔍 检测文件类型: {file_path.name} -> {real_type}")

            loader = _create_loader(file_path, real_type, category)
            if loader is None:
                continue

            documents = loader.load()
            all_documents.extend(documents)
        except Exception as e:
            print(f"⚠️  加载文件 {file_path} 时出错: {e}")
            continue

    print(f"📚 总共加载了 {len(all_documents)} 个文档片段")
    return all_documents


def _create_loader(
    file_path: Path,
    file_type: str,
    category: Optional[Literal["policies", "cases"]],
) -> Optional[BaseDocumentLoader]:
    """根据文件类型创建对应的加载器"""
    loader_map = {
        'pdf': PDFLoader,
        'doc': DOCLoader,
        'docx': DOCXLoader,
        'pptx': PPTXLoader,
        'markdown': MarkdownLoader,
        'txt': TextFileLoader,
    }

    loader_class = loader_map.get(file_type)
    if loader_class is None:
        if file_type == 'ppt':
            print(f"⚠️  暂不支持 PPT 格式，请转换为 PPTX: {file_path.name}")
        else:
            print(f"⚠️  不支持的文件类型: {file_type}，跳过: {file_path.name}")
        return None

    return loader_class(file_path, category=category)


def load_knowledge_base(
    data_dir: str | Path,
    categories: Optional[list[Literal["policies", "cases"]]] = None,
) -> list[Document]:
    """加载知识库（支持分类）"""
    data_dir = Path(data_dir)

    if categories is None:
        categories = [
            item.name
            for item in data_dir.iterdir()
            if item.is_dir() and item.name in ["policies", "cases"]
        ]

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
            category=category,
        )
        all_documents.extend(documents)

    print(f"\n{'='*60}")
    print(f"✅ 知识库加载完成！")
    print(f"   - 总文档数: {len(all_documents)}")
    print(f"   - 类别: {', '.join(categories)}")
    print(f"{'='*60}\n")

    return all_documents

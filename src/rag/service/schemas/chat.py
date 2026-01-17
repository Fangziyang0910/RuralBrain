"""
Planning Service 请求/响应数据模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 请求模型 ====================
class PlanningChatRequest(BaseModel):
    """规划咨询聊天请求"""
    message: str = Field(..., description="用户问题", min_length=1)
    thread_id: Optional[str] = Field(None, description="对话线程ID")
    mode: str = Field(
        "auto",
        description="工作模式: auto(自动选择)/fast(快速浏览)/deep(深度分析)",
        pattern="^(auto|fast|deep)$"
    )


class DocumentListRequest(BaseModel):
    """文档列表查询请求（预留扩展）"""
    source_type: Optional[str] = Field(None, description="文档类型: policies/cases")


# ==================== 响应模型 ====================
class ToolCall(BaseModel):
    """工具调用信息"""
    name: str = Field(..., description="工具名称")
    arguments: str = Field(..., description="调用参数")


class PlanningChatResponse(BaseModel):
    """规划咨询聊天响应（非流式）"""
    response: str = Field(..., description="AI 回复内容")
    tools_used: List[str] = Field(default_factory=list, description="使用的工具列表")
    actual_mode: str = Field(..., description="实际使用的工作模式")
    thread_id: str = Field(..., description="对话线程ID")
    sources_count: int = Field(default=0, description="引用的文档数量")


class DocumentInfo(BaseModel):
    """单个文档信息"""
    source: str = Field(..., description="文档文件名")
    type: str = Field(..., description="文档类型: policy/case")
    chunk_count: int = Field(..., description="切片数量")
    preview: str = Field(..., description="内容预览（前100字）")


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[DocumentInfo] = Field(..., description="可用文档列表")
    total_count: int = Field(..., description="文档总数")
    total_chunks: int = Field(..., description="总切片数")


class DocumentSummaryResponse(BaseModel):
    """文档执行摘要响应"""
    source: str = Field(..., description="文档文件名")
    executive_summary: str = Field(..., description="200字执行摘要")


class ChapterInfo(BaseModel):
    """章节信息"""
    header: str = Field(..., description="章节标题")
    summary: str = Field(..., description="章节摘要")


class ChapterListResponse(BaseModel):
    """章节列表响应"""
    source: str = Field(..., description="文档文件名")
    chapters: List[ChapterInfo] = Field(..., description="章节列表")


# ==================== 健康检查模型 ====================
class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态: healthy/unhealthy")
    service: str = Field(..., description="服务名称")
    version: str = Field(..., description="服务版本")
    knowledge_base_loaded: bool = Field(..., description="知识库是否已加载")


# ==================== 错误响应模型 ====================
class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误详情")
    detail: Optional[str] = Field(None, description="详细信息")

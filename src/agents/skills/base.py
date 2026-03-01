"""
技能抽象层

基于 LangChain Skills 模式，定义可按需加载的专门能力。
"""
from typing import List, Optional
from pydantic import BaseModel, Field

from ..middleware.tool_lifecycle import TTLConfig


class Skill(BaseModel):
    """
    技能数据类 - 基于 LangChain Skills 模式

    专注于渐进式披露（Progressive Disclosure）：
    - 系统提示词中只包含简短描述
    - 完整内容通过 load_skill 工具按需加载

    使用 Pydantic 提供自动验证和类型安全。

    Attributes:
        name: 技能唯一标识
        description: 简短描述（1-2 句话，显示在系统提示词中）
        content: 完整内容（按需加载）
        tool_names: 关联的工具名称列表（用于动态工具注册）
        references: 参考资源列表（用于参考信息感知）
        ttl_config: TTL 配置（可选，用于工具生命周期管理）
    """

    # 基础信息（用于渐进式披露）
    name: str = Field(..., description="技能唯一标识")
    description: str = Field(..., min_length=1, description="简短描述（1-2 句话）")

    # 完整内容（按需加载）
    content: str = Field(default="", description="完整技能内容")

    # 关联工具（工具名称列表，用于动态工具注册）
    tool_names: List[str] = Field(default_factory=list, description="关联的工具名称列表")

    # 参考资源（用于参考信息感知扩展）
    references: List[str] = Field(default_factory=list, description="参考资源列表")

    # TTL 配置（用于工具生命周期管理）
    ttl_config: Optional[TTLConfig] = Field(None, description="TTL 配置")

    model_config = {"extra": "ignore"}

    def get_description_for_prompt(self) -> str:
        """
        生成用于系统提示词的技能描述

        这是 Progressive Disclosure 的核心：
        只在系统提示词中包含简短描述，完整内容通过 load_skill 工具按需加载。

        Returns:
            格式化的技能描述字符串
        """
        return f"- **{self.name}**: {self.description}"

    def get_ttl_config(self) -> "TTLConfig":
        """
        获取 TTL 配置

        如果技能没有配置 TTL，返回默认配置。

        Returns:
            TTLConfig 实例
        """
        from ..middleware.tool_lifecycle import TTLConfig
        from ...config import DEFAULT_TOOL_TTL, DEFAULT_TOOL_EXTENSION

        if self.ttl_config is None:
            return TTLConfig(base_ttl=DEFAULT_TOOL_TTL, extension=DEFAULT_TOOL_EXTENSION)
        return self.ttl_config


# 重建模型以正确处理 TTLConfig 类型引用（Pydantic v2 要求）
Skill.model_rebuild()

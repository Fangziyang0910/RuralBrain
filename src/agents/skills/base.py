"""
技能抽象层

基于 LangChain Skills 模式，定义可按需加载的专门能力。
"""

from typing import List
from dataclasses import dataclass, field
from langchain_core.tools import BaseTool


@dataclass
class Skill:
    """
    技能抽象基类 - 简化版本

    基于 LangChain Skills 模式，专注于渐进式披露。

    Attributes:
        name: 技能唯一标识
        description: 简短描述（1-2 句话，显示在系统提示词中）
        content: 完整内容（按需加载，通过 load_skill 工具）
        tools: 技能专属工具列表
    """

    # 基础信息（用于渐进式披露）
    name: str
    description: str

    # 完整内容（按需加载）
    content: str = ""

    # 关联工具
    tools: List[BaseTool] = field(default_factory=list)

    def get_prompt_addendum(self) -> str:
        """
        生成用于系统提示词的简短描述。

        这是 Progressive Disclosure 的核心：
        只在系统提示词中包含简短描述，完整内容通过 load_skill 工具按需加载。

        Returns:
            格式化的技能描述字符串
        """
        return f"- **{self.name}**: {self.description}"

    def get_full_content(self) -> str:
        """
        获取技能的完整内容（通过 load_skill 工具调用）。

        Returns:
            技能的完整内容
        """
        return self.content or self.description

    def get_tool_names(self) -> List[str]:
        """获取技能关联的工具名称列表"""
        return [tool.name for tool in self.tools]

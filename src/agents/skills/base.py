"""
技能抽象层

基于 LangChain Skills 模式，定义可按需加载的专门能力。
"""
from typing import List
from dataclasses import dataclass, field


@dataclass
class Skill:
    """
    技能数据类 - 基于 LangChain Skills 模式

    专注于渐进式披露（Progressive Disclosure）：
    - 系统提示词中只包含简短描述
    - 完整内容通过 load_skill 工具按需加载

    Attributes:
        name: 技能唯一标识
        description: 简短描述（1-2 句话，显示在系统提示词中）
        content: 完整内容（按需加载）
        tool_names: 关联的工具名称列表（用于动态工具注册）
        references: 参考资源列表（用于参考信息感知）
    """

    # 基础信息（用于渐进式披露）
    name: str
    description: str

    # 完整内容（按需加载）
    content: str = ""

    # 关联工具（工具名称列表，用于动态工具注册）
    tool_names: List[str] = field(default_factory=list)

    # 参考资源（用于参考信息感知扩展）
    references: List[str] = field(default_factory=list)

    def get_description_for_prompt(self) -> str:
        """
        生成用于系统提示词的技能描述

        这是 Progressive Disclosure 的核心：
        只在系统提示词中包含简短描述，完整内容通过 load_skill 工具按需加载。

        Returns:
            格式化的技能描述字符串
        """
        return f"- **{self.name}**: {self.description}"

"""
技能抽象层

基于 LangChain Skills 模式，定义可按需加载的专门能力。
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from langchain_core.tools import BaseTool


@dataclass
class Skill:
    """
    技能抽象基类

    基于 LangChain Skills 模式，定义可按需加载的专门能力。

    Attributes:
        name: 技能唯一标识
        description: 简短描述（1-2 句话，显示在系统提示词中）
        category: 技能分类（detection/planning/analysis）
        version: 技能版本
        system_prompt: 完整系统提示词（按需加载，通过 load_skill 工具）
        examples: Few-shot 示例列表
        constraints: 约束条件列表
        tools: 技能专属工具列表
        metadata: 额外元数据
        enabled: 是否启用
    """

    # 基础信息
    name: str
    description: str
    category: str
    version: str = "1.0.0"

    # 渐进式披露内容
    system_prompt: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    # 关联工具
    tools: List[BaseTool] = field(default_factory=list)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

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
            包含完整提示词、约束、示例和工具说明的内容
        """
        parts = [f"# {self.name} 技能\n"]

        if self.system_prompt:
            parts.append(self.system_prompt)

        if self.constraints:
            parts.append("\n## 约束条件\n")
            parts.extend(f"- {c}" for c in self.constraints)

        if self.examples:
            parts.append("\n## 示例\n")
            for i, ex in enumerate(self.examples, 1):
                parts.append(f"{i}. {ex}")

        if self.tools:
            parts.append("\n## 可用工具\n")
            for tool in self.tools:
                parts.append(f"- **{tool.name}**: {tool.description}")

        return "\n".join(parts)

    def get_tool_names(self) -> List[str]:
        """获取技能关联的工具名称列表"""
        return [tool.name for tool in self.tools]

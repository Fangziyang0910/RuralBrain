"""
模式感知中间件（简化版）

提供模式配置和工具调用次数限制信息，供 Agent 和路由使用。
注意：由于 LangChain ModelRequest API 的限制，模式信息现在通过
build_system_prompt_with_mode 函数动态注入到系统提示词中。
"""
from typing import Optional, Dict, Any


class ModeAwareMiddleware:
    """
    模式感知中间件（简化版）

    功能：
    1. 提供模式配置信息
    2. 生成模式相关的系统提示词片段
    3. 不再尝试注入到 ModelRequest（避免 API 兼容性问题）

    模式映射：
    - fast: 快速浏览模式（最多 2 次工具调用）
    - deep: 深度分析模式（最多 5 次工具调用）
    - auto: 自动模式（无限制）
    """

    # 模式配置映射
    MODE_CONFIGS = {
        "fast": {
            "max_tool_calls": 2,
            "description": "快速浏览模式",
            "guidance": "优先使用摘要和要点工具，避免深入阅读完整文档"
        },
        "deep": {
            "max_tool_calls": 5,
            "description": "深度分析模式",
            "guidance": "可以使用完整工具链，包括章节内容和全文检索"
        },
        "auto": {
            "max_tool_calls": None,  # 无限制
            "description": "自动模式",
            "guidance": "根据问题复杂度自主选择合适的工具"
        },
    }

    def __init__(self, default_mode: str = "auto"):
        """
        初始化模式感知中间件

        Args:
            default_mode: 默认模式（fast/deep/auto）
        """
        if default_mode not in self.MODE_CONFIGS:
            raise ValueError(
                f"无效的默认模式: {default_mode}. "
                f"可选: {', '.join(self.MODE_CONFIGS.keys())}"
            )

        self.default_mode = default_mode
        self.current_mode = default_mode

    def get_mode_config(self, mode: str) -> Dict[str, Any]:
        """
        获取指定模式的配置

        Args:
            mode: 模式名称（fast/deep/auto）

        Returns:
            模式配置字典
        """
        return self.MODE_CONFIGS.get(mode, self.MODE_CONFIGS["auto"])

    def get_mode_prompt_addendum(self, mode: str) -> str:
        """
        生成模式相关的系统提示词片段

        Args:
            mode: 模式名称

        Returns:
            模式提示词片段
        """
        config = self.get_mode_config(mode)

        mode_instruction = "\n\n<current_mode>\n"
        mode_instruction += f"当前工作模式: {config['description']}\n"

        # 添加工具调用限制指导
        if config["max_tool_calls"] is not None:
            mode_instruction += f"工具调用限制: 最多 {config['max_tool_calls']} 次\n"
            mode_instruction += f"工作指导: {config['guidance']}\n"
        else:
            mode_instruction += f"工作指导: {config['guidance']}\n"

        mode_instruction += "</current_mode>\n"

        return mode_instruction

    def get_max_tool_calls(self, mode: Optional[str] = None) -> Optional[int]:
        """
        获取指定模式的工具调用次数限制

        Args:
            mode: 模式名称，如果为 None 则使用当前模式

        Returns:
            最大工具调用次数，None 表示无限制
        """
        if mode is None:
            mode = self.current_mode

        config = self.get_mode_config(mode)
        return config["max_tool_calls"]

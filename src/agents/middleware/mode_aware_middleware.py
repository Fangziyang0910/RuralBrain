"""
模式感知中间件

根据用户选择的模式动态限制工具调用次数和注入模式信息到系统提示词。
"""
from typing import Callable, Optional, Dict, Any
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage


class ModeAwareMiddleware(AgentMiddleware):
    """
    模式感知中间件

    功能：
    1. 根据运行时配置的模式注入信息到系统提示词
    2. 提供模式配置供其他中间件使用

    模式映射：
    - fast: 快速浏览模式（最多 2 次工具调用）
    - deep: 深度分析模式（最多 5 次工具调用）
    - auto: 自动模式（无限制）

    Attributes:
        default_mode: 默认模式
        current_mode: 当前模式
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

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """
        在模型调用前注入模式信息到系统提示词

        Args:
            request: 模型请求
            handler: 下一个处理器

        Returns:
            模型响应
        """
        # 从 state 中获取模式（从 config 传入）
        mode = request.state.get("mode", self.default_mode)

        # 更新当前模式
        if mode in self.MODE_CONFIGS:
            self.current_mode = mode
        else:
            self.current_mode = self.default_mode
            mode = self.default_mode

        # 获取模式配置
        mode_config = self.get_mode_config(mode)

        # 构建模式信息
        mode_instruction = f"\n\n<current_mode>\n"
        mode_instruction += f"当前工作模式: {mode_config['description']}\n"

        # 添加工具调用限制指导
        if mode_config["max_tool_calls"] is not None:
            mode_instruction += f"工具调用限制: 最多 {mode_config['max_tool_calls']} 次\n"
            mode_instruction += f"工作指导: {mode_config['guidance']}\n"
        else:
            mode_instruction += f"工作指导: {mode_config['guidance']}\n"

        mode_instruction += "</current_mode>\n"

        # 附加到系统消息
        try:
            # 尝试处理 content_blocks 格式
            if hasattr(request.system_message, 'content_blocks'):
                new_content = list(request.system_message.content_blocks) + [
                    {"type": "text", "text": mode_instruction}
                ]
            else:
                # 处理普通字符串格式
                current_content = request.system_message.content
                new_content = [{"type": "text", "text": current_content + mode_instruction}]
        except Exception:
            # 如果都失败了，直接追加到字符串
            current_content = str(request.system_message.content)
            new_content = [{"type": "text", "text": current_content + mode_instruction}]

        new_system_message = SystemMessage(content=new_content)
        modified_request = request.override(system_message=new_system_message)

        return handler(modified_request)

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


class ToolCallLimitMiddleware(AgentMiddleware):
    """
    工具调用限制中间件

    监控并限制工具调用次数。当达到限制时，阻止进一步的工具调用。

    注意：这是一个简化的实现，用于演示概念。
    在生产环境中，应该在 Agent 层面实现更精确的调用控制。

    Attributes:
        max_tool_calls: 最大工具调用次数，None 表示无限制
        call_count: 当前调用次数计数器
    """

    def __init__(self, max_tool_calls: Optional[int] = None):
        """
        初始化工具调用限制中间件

        Args:
            max_tool_calls: 最大工具调用次数，None 表示无限制
        """
        self.max_tool_calls = max_tool_calls
        self.call_count = 0

    def reset(self):
        """重置调用计数器"""
        self.call_count = 0

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """
        在每次模型调用前检查工具调用次数

        注意：这里的实现是简化的。真正的工具调用限制需要在
        Agent 运行时层面实现，而不是在模型调用层面。
        """
        # 重置计数器（每次新的模型调用）
        self.reset()

        return handler(request)

    def should_allow_tool_call(self) -> bool:
        """
        检查是否应该允许工具调用

        Returns:
            True 如果允许，False 如果已达到限制
        """
        if self.max_tool_calls is None:
            return True

        self.call_count += 1
        return self.call_count <= self.max_tool_calls

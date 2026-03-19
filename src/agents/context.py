"""
Agent 运行时上下文定义

用于在 Agent 执行过程中传递用户配置（如模型选择）
"""
from dataclasses import dataclass


@dataclass
class AgentContext:
    """
    Agent 运行时上下文

    通过 LangChain create_agent 的 context_schema 参数注册，
    在 middleware 中通过 request.runtime.context 访问。

    Attributes:
        model_id: 用户选择的模型 ID，默认为 "deepseek"
    """
    model_id: str = "deepseek"
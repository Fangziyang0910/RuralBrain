"""农业智能代理模块

该模块包含各类农业相关的智能代理实现。
"""

from .pest_detection_agent import agent as pest_detection_agent
from .rice_detection_agent import agent as rice_detection_agent

__all__ = ["pest_detection_agent", "rice_detection_agent"]

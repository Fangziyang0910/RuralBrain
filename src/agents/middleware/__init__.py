"""
中间件模块

基于 LangChain AgentMiddleware 实现：
- SkillMiddleware: 技能渐进式披露（支持动态工具注册）
"""

from .skill_middleware import SkillMiddleware

__all__ = [
    "SkillMiddleware",
]

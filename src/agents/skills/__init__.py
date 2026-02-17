"""
技能模块

基于 LangChain Skills 模式，定义可按需加载的专门能力。
配置通过 YAML 文件管理，由 SkillRegistry 统一加载。
"""

from .base import Skill
from .registry import SkillRegistry, get_registry, reset_registry

__all__ = [
    "Skill",
    "SkillRegistry",
    "get_registry",
    "reset_registry",
]

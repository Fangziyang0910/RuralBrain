"""
技能模块

基于 LangChain Skills 模式，定义可按需加载的专门能力。
"""

from .base import Skill
from .detection_skills import create_all_detection_skills
from .planning_skills import create_all_planning_skills
from .pricing_skills import create_all_pricing_skills
from .farm_inspection_skills import create_all_farm_inspection_skills
from .orchestration_skills import create_all_orchestration_skills

__all__ = [
    "Skill",
    "create_all_detection_skills",
    "create_all_planning_skills",
    "create_all_pricing_skills",
    "create_all_farm_inspection_skills",
    "create_all_orchestration_skills",
]

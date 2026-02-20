"""
技能注册中心

集中管理所有技能配置，提供统一的技能加载接口。
"""
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from .base import Skill


class SkillRegistry:
    """技能注册中心 - 统一管理所有技能"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        初始化技能注册中心

        Args:
            config_dir: YAML 配置文件目录，默认为 src/agents/skills/configs/
        """
        if config_dir is None:
            config_dir = Path(__file__).parent / "configs"
        self.config_dir = config_dir
        self._skills: Dict[str, Skill] = {}
        self._load_all_configs()

    def _load_all_configs(self):
        """从 YAML 文件加载所有技能配置"""
        if not self.config_dir.exists():
            # 如果配置目录不存在，不加载任何配置
            return

        for yaml_file in self.config_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data:
                        for skill_name, skill_data in data.items():
                            # 确保 name 字段存在
                            skill_data["name"] = skill_name
                            # 直接创建 Skill 对象
                            self._skills[skill_name] = Skill(**skill_data)
            except Exception as e:
                print(f"警告：加载配置文件 {yaml_file} 失败: {e}")

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """获取指定技能"""
        return self._skills.get(skill_name)

    def get_all_skills(self) -> List[Skill]:
        """获取所有技能"""
        return list(self._skills.values())

    def get_skill_descriptions(self) -> str:
        """
        获取所有技能的简短描述

        用于 Progressive Disclosure，注入到系统提示词中。
        """
        return "\n".join(
            skill.get_description_for_prompt()
            for skill in self._skills.values()
        )

    def load_content(self, skill_name: str) -> str:
        """
        加载技能的完整内容

        Args:
            skill_name: 技能名称

        Returns:
            技能的完整内容
        """
        skill = self.get_skill(skill_name)
        if not skill:
            raise ValueError(f"技能 '{skill_name}' 未找到")

        return skill.content or f"# {skill.name}\n\n{skill.description}"

    def list_skill_names(self) -> List[str]:
        """列出所有可用技能名称

        Returns:
            所有技能名称的列表
        """
        return list(self._skills.keys())

    def reload(self):
        """重新加载技能配置（生产环境考虑）"""
        self._skills.clear()
        self._load_all_configs()


# 全局单例
_global_registry: Optional[SkillRegistry] = None


def get_registry() -> SkillRegistry:
    """获取全局技能注册中心单例"""
    global _global_registry
    if _global_registry is None:
        _global_registry = SkillRegistry()
    return _global_registry


def reset_registry():
    """重置全局注册中心（主要用于测试）"""
    global _global_registry
    _global_registry = None

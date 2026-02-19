"""
技能注册中心

集中管理所有技能配置，提供统一的技能创建和加载接口。
"""
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import yaml

from .base import Skill


@dataclass
class SkillConfigData:
    """技能配置数据（从 YAML 加载）"""
    name: str
    description: str
    content: str = ""
    tools: List[str] = field(default_factory=list)


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
        self._configs: Dict[str, SkillConfigData] = {}
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
                            skill_data["name"] = skill_name
                            self._configs[skill_name] = SkillConfigData(**skill_data)
            except Exception as e:
                print(f"警告：加载配置文件 {yaml_file} 失败: {e}")

    def get_config(self, skill_name: str) -> Optional[SkillConfigData]:
        """获取技能配置"""
        return self._configs.get(skill_name)

    def get_all_configs(self) -> Dict[str, SkillConfigData]:
        """获取所有技能配置"""
        return self._configs.copy()

    def get_skill_descriptions(self) -> str:
        """
        获取所有技能的简短描述

        用于 Progressive Disclosure，注入到系统提示词中。
        """
        return "\n".join(
            f"- **{config.name}**: {config.description}"
            for config in self._configs.values()
        )

    def load_content(self, skill_name: str) -> str:
        """
        加载技能的完整内容

        Args:
            skill_name: 技能名称

        Returns:
            技能的完整内容
        """
        config = self.get_config(skill_name)
        if not config:
            raise ValueError(f"技能 '{skill_name}' 未找到")

        return config.content or f"# {config.name}\n\n{config.description}"

    def create_skill(
        self,
        skill_name: str,
        tools_map: Dict[str, object],
    ) -> Skill:
        """
        根据配置创建技能对象

        Args:
            skill_name: 技能名称
            tools_map: 工具名称到工具对象的映射

        Returns:
            Skill 对象
        """
        config = self.get_config(skill_name)
        if not config:
            raise ValueError(f"技能 '{skill_name}' 未找到")

        # 解析工具
        tools = [tools_map[name] for name in config.tools if name in tools_map]

        return Skill(
            name=config.name,
            description=config.description,
            content=config.content,
            tools=tools,
        )

    def create_all_skills(self, tools_map: Dict[str, object]) -> List[Skill]:
        """
        创建所有技能

        Args:
            tools_map: 工具名称到工具对象的映射

        Returns:
            所有技能的列表
        """
        return [
            self.create_skill(name, tools_map)
            for name in self._configs.keys()
        ]

    def list_skill_names(self) -> List[str]:
        """列出所有可用技能名称

        Returns:
            所有技能名称的列表
        """
        return list(self._configs.keys())


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

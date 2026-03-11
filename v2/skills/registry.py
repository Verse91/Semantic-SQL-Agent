"""
Skill 注册表
用于注册和获取 Skills
"""
from typing import Dict, Optional
from .base import BaseSkill


class SkillRegistry:
    """Skill 注册表"""
    
    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
    
    def register(self, skill: BaseSkill) -> None:
        """
        注册 Skill
        
        Args:
            skill: Skill 实例
        """
        self.skills[skill.name] = skill
    
    def get(self, name: str) -> Optional[BaseSkill]:
        """
        获取 Skill
        
        Args:
            name: Skill 名称
            
        Returns:
            Skill 实例，不存在返回 None
        """
        return self.skills.get(name)
    
    def list_skills(self) -> list:
        """列出所有注册的 Skill"""
        return list(self.skills.keys())
    
    def clear(self) -> None:
        """清空注册表"""
        self.skills.clear()


# 全局注册表实例
_global_registry = SkillRegistry()


def get_registry() -> SkillRegistry:
    """获取全局 Skill 注册表"""
    return _global_registry

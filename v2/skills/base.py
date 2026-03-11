"""
Skill 基类
所有 Skill 继承此基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseSkill(ABC):
    """Skill 基类"""
    
    name: str = ""
    description: str = ""
    
    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行 Skill
        
        Args:
            state: Agent 状态
            
        Returns:
            更新后的 state
        """
        raise NotImplementedError
    
    def __repr__(self):
        return f"<Skill: {self.name}>"

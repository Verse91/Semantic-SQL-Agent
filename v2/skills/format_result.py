"""
结果格式化 Skill
"""
from typing import Dict, Any
from skills.base import BaseSkill


class FormatResultSkill(BaseSkill):
    """结果格式化 Skill"""
    
    name = "format_result"
    description = "将 SQL 执行结果格式化为 JSON"
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """格式化结果"""
        result = state.get("execution_result", {})
        
        if result is None:
            state["execution_result"] = {
                "data": [],
                "columns": [],
                "row_count": 0,
                "formatted": "[]"
            }
            return state
        
        # 转换为标准格式
        formatted = {
            "data": result.get("data", []),
            "columns": result.get("columns", []),
            "row_count": result.get("row_count", 0),
            "execution_time_ms": result.get("execution_time_ms", 0),
            "formatted": self._to_json(result.get("data", []))
        }
        
        state["execution_result"] = formatted
        return state
    
    def _to_json(self, data: list) -> str:
        """转换为 JSON 字符串"""
        import json
        try:
            return json.dumps(data, ensure_ascii=False, indent=2)
        except:
            return "[]"


# 实例
format_result_skill = FormatResultSkill()

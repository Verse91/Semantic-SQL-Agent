"""
SQL 校验 Skill
"""
from typing import Dict, Any
from skills.base import BaseSkill


class ValidateSQLSkill(BaseSkill):
    """SQL 校验 Skill"""
    
    name = "validate_sql"
    description = "校验 SQL 安全性，仅允许 SELECT"
    
    # 禁止的 SQL 关键字
    FORBIDDEN_KEYWORDS = [
        "drop", "delete", "update", "insert", "alter",
        "truncate", "create", "exec", "execute", "call"
    ]
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """校验 SQL"""
        sql = state.get("generated_sql", "")
        
        if not sql:
            state["error"] = "No SQL to validate"
            return state
        
        sql_lower = sql.lower().strip()
        
        # 检查是否以 SELECT 开头
        if not sql_lower.startswith("select"):
            state["error"] = "Only SELECT queries are allowed"
            return state
        
        # 检查禁止的关键字
        for keyword in self.FORBIDDEN_KEYWORDS:
            if sql_lower.startswith(keyword):
                state["error"] = f"Keyword '{keyword}' is not allowed"
                return state
        
        # 校验通过
        state["validated_sql"] = sql
        return state


# 实例
validate_sql_skill = ValidateSQLSkill()

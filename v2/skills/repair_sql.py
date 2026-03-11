"""
SQL 修复 Skill
"""
import os
import sys
from typing import Dict, Any
from skills.base import BaseSkill

# 添加父项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


class RepairSQLSkill(BaseSkill):
    """SQL 修复 Skill"""
    
    name = "repair_sql"
    description = "根据错误信息自动修复 SQL"
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """修复 SQL"""
        original_sql = state.get("validated_sql", "")
        error = state.get("error", "")
        schema_context = state.get("schema_context", "")
        
        if not error:
            state["error"] = "No error to repair"
            return state
        
        # 构建修复 prompt
        from prompts.repair_sql_prompt import build_repair_sql_prompt
        prompt = build_repair_sql_prompt(
            original_sql=original_sql,
            error_message=error,
            schema_context=schema_context
        )
        
        # 调用 LLM 修复
        from app.llm_service import generate_sql as llm_generate_sql
        result = llm_generate_sql(prompt)
        
        if result.get("error"):
            state["error"] = f"Repair failed: {result['error']}"
        else:
            fixed_sql = result.get("sql", "")
            state["generated_sql"] = fixed_sql
            state["validated_sql"] = fixed_sql
            state["error"] = None
        
        return state


# 实例
repair_sql_skill = RepairSQLSkill()

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

# 导入 trace 模块
try:
    from tracing import log_repair_sql
    HAS_TRACING = True
except ImportError:
    HAS_TRACING = False


class RepairSQLSkill(BaseSkill):
    """SQL 修复 Skill"""
    
    name = "repair_sql"
    description = "根据错误信息自动修复 SQL"
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """修复 SQL（带重试循环）"""
        original_sql = state.get("validated_sql", "")
        error = state.get("error", "")
        schema_context = state.get("schema_context", "")
        max_retries = state.get("retry_count", 0) + 1  # 最多重试 retry_count + 1 次
        
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
        
        # 调用 LLM 修复（带重试循环）
        from v1.llm_service import generate_sql as llm_generate_sql
        fixed_sql = ""
        last_error = ""
        
        for attempt in range(max_retries):
            result = llm_generate_sql(prompt)
            
            if result.get("error"):
                last_error = result["error"]
                continue  # 重试
            
            fixed_sql = result.get("sql", "")
            if fixed_sql:
                break  # 成功，跳出循环
            last_error = "LLM returned empty SQL"
        
        if fixed_sql and not last_error:
            state["generated_sql"] = fixed_sql
            state["validated_sql"] = fixed_sql
            state["error"] = None
            
            # Trace logging
            if HAS_TRACING:
                log_repair_sql(original_sql, fixed_sql, error, attempt + 1)
        else:
            state["error"] = f"Repair failed after {max_retries} attempts: {last_error}"
            
            # Trace logging
            if HAS_TRACING:
                log_repair_sql(original_sql, "", error, max_retries)
        
        return state


# 实例
repair_sql_skill = RepairSQLSkill()

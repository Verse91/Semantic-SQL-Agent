"""
SQL 生成 Skill (支持 Query Plan)
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
    from tracing import log_generate_sql
    HAS_TRACING = True
except ImportError:
    HAS_TRACING = False


class GenerateSQLSkill(BaseSkill):
    """SQL 生成 Skill"""
    
    name = "generate_sql"
    description = "将自然语言或 Query Plan 转换为 SQL 查询"
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """生成 SQL"""
        from prompts.generate_sql_prompt import build_generate_sql_prompt
        
        user_query = state.get("user_query", "")
        schema_context = state.get("schema_context", "")
        conversation_history = state.get("conversation_history", [])
        query_plan = state.get("query_plan", {})
        
        # 构建 prompt (支持 Query Plan)
        prompt = build_generate_sql_prompt(
            user_query=user_query,
            schema_context=schema_context,
            conversation_history=conversation_history,
            query_plan=query_plan
        )
        
        # 直接调用 MiniMax API
        sql = self._call_minimax(prompt)
        
        # Trace logging (always log, whether success or failure)
        if HAS_TRACING:
            log_generate_sql(state.get("retrieved_tables", []), sql if sql else "FAILED")
        
        if sql:
            state["generated_sql"] = sql
            state["error"] = None
        else:
            state["generated_sql"] = ""
            state["error"] = "Failed to generate SQL"
        
        return state
    
    def _call_minimax(self, prompt: str) -> str:
        """调用 MiniMax API"""
        import requests
        
        api_key = os.getenv("MINIMAX_API_KEY")
        if not api_key:
            return ""
        
        url = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "MiniMax-M2.7",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        
        try:
            resp = requests.post(url, json=data, headers=headers, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("choices") and len(result.get("choices", [])) > 0:
                msg = result["choices"][0].get("message", {})
                sql = msg.get("content", "")
                if sql:
                    # 清理 SQL (去除 markdown 代码块)
                    sql = sql.strip()
                    if sql.startswith("```sql"):
                        sql = sql[6:]
                    elif sql.startswith("```"):
                        sql = sql[3:]
                    if sql.endswith("```"):
                        sql = sql[:-3]
                    return sql.strip()
        except Exception as e:
            print(f"Minimax API error: {e}")
        
        return ""


# 实例
generate_sql_skill = GenerateSQLSkill()

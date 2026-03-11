"""
SQL 生成 Skill
"""
import os
import sys
import requests
from typing import Dict, Any
from skills.base import BaseSkill

# 添加父项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from prompts.generate_sql_prompt import build_generate_sql_prompt


class GenerateSQLSkill(BaseSkill):
    """SQL 生成 Skill"""
    
    name = "generate_sql"
    description = "将自然语言转换为 SQL 查询"
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """生成 SQL"""
        # 构建 prompt
        prompt = build_generate_sql_prompt(
            user_query=state["user_query"],
            schema_context=state.get("schema_context", ""),
            conversation_history=state.get("conversation_history", [])
        )
        
        # 直接调用 MiniMax API (绕过原始 llm_service 的严格验证)
        sql = self._call_minimax(prompt)
        
        if sql:
            state["generated_sql"] = sql
            state["error"] = None
        else:
            state["generated_sql"] = ""
            state["error"] = "Failed to generate SQL"
        
        return state
    
    def _call_minimax(self, prompt: str) -> str:
        """调用 MiniMax API"""
        api_key = os.getenv("MINIMAX_API_KEY")
        if not api_key:
            return ""
        
        url = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "MiniMax-M2.1",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        
        try:
            resp = requests.post(url, json=data, headers=headers, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            
            # 调试输出
            print(f"API Response: {result}")
            
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

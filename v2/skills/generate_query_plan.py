"""
Query Plan Generator Skill
根据 FS JSON 生成查询计划
"""
import os
import sys
import json
import re
from typing import Dict, Any
from skills.base import BaseSkill

# 添加父项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


class GenerateQueryPlanSkill(BaseSkill):
    """Query Plan 生成 Skill"""
    
    name = "generate_query_plan"
    description = "根据 FS 解析结果生成查询计划"
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """生成 Query Plan"""
        fs_json = state.get("fs_json", {})
        schema_context = state.get("schema_context", "")
        
        if not fs_json:
            state["error"] = "No FS JSON to generate query plan"
            return state
        
        # 构建 prompt
        from prompts.query_plan_prompt import build_query_plan_prompt
        prompt = build_query_plan_prompt(fs_json, schema_context)
        
        # 调用 LLM 生成
        result = self._call_llm(prompt)
        
        if result:
            try:
                query_plan = self._extract_json(result)
                state["query_plan"] = query_plan
                state["error"] = None
            except Exception as e:
                state["query_plan"] = {}
                state["error"] = f"Failed to parse query plan: {str(e)}"
        else:
            state["query_plan"] = {}
            state["error"] = "Failed to call LLM"
        
        return state
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
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
            "model": "MiniMax-M2.1",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        
        try:
            resp = requests.post(url, json=data, headers=headers, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            
            if result.get("choices") and len(result.get("choices", [])) > 0:
                content = result["choices"][0].get("message", {}).get("content", "")
                return content
        except Exception as e:
            print(f"LLM call error: {e}")
        
        return ""
    
    def _extract_json(self, text: str) -> dict:
        """从文本中提取 JSON"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except:
            pass
        
        # 尝试提取代码块
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        
        # 尝试找到 { } 包围的内容
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        
        # 返回默认结构
        return {
            "tables": [],
            "joins": [],
            "metrics": [],
            "filters": [],
            "group_by": [],
            "order_by": [],
            "limit": 1000
        }


# 实例
generate_query_plan_skill = GenerateQueryPlanSkill()

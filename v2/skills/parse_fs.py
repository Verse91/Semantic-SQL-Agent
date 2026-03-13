"""
FS Parser Skill
将 FS 文档解析为结构化 JSON
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


class ParseFSSkill(BaseSkill):
    """FS 解析 Skill"""
    
    name = "parse_fs"
    description = "将 FS 报表文档解析为结构化 JSON"
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """解析 FS 文档"""
        fs_document = state.get("fs_document", "")
        
        if not fs_document:
            state["error"] = "No FS document to parse"
            return state
        
        # 构建 prompt
        from prompts.parse_fs_prompt import build_parse_fs_prompt
        prompt = build_parse_fs_prompt(fs_document)
        
        # 调用 LLM 解析
        result = self._call_llm(prompt)
        
        if result:
            try:
                # 尝试提取 JSON
                fs_json = self._extract_json(result)
                state["fs_json"] = fs_json
                state["error"] = None
            except Exception as e:
                state["fs_json"] = {}
                state["error"] = f"Failed to parse FS: {str(e)}"
        else:
            state["fs_json"] = {}
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
        
        # 尝试提取 ```json 或 ``` 块
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
            "report_name": "",
            "tables": [],
            "dimensions": [],
            "metrics": [],
            "filters": []
        }


# 实例
parse_fs_skill = ParseFSSkill()

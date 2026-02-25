import requests
import os
import json
from typing import Dict, Any, Optional
from .config import DATABASE_SCHEMA


# Prompt 模板 - 升级版
SQL_GENERATOR_PROMPT = """你是一个专业SQL数据分析师。

已知表结构：
- mysql.sap.mara (物料主数据): matnr, ersda, ernam, laeda, aenam, vpsta, pstat, lvorm, mtart, matkl
- postgresql.public.makt (物料描述): matnr, spras(语言代码E=英文, C=中文), maktx(描述)

注意：不同表在不同数据库！
- mara 在 mysql catalog
- makt 在 postgresql catalog

规则：
1. 只允许生成 SELECT 查询
2. 禁止 DROP、DELETE、UPDATE、INSERT、ALTER、TRUNCATE
3. 中文名称在 postgresql 的 makt.maktx，连接用 matnr
4. 中文语言代码 spras = 'C'
5. Trino SQL 跨库查询用 catalog.schema.table 格式
6. 字段名和别名只能用英文，不能用中文！
7. 只返回SQL语句，不要任何解释

用户问题：{user_input}

只返回SQL。"""


class LLMError(Exception):
    """LLM 调用异常"""
    pass


# MiniMax API 配置
MINIMAX_API_KEY = "sk-cp-WmhpWGprQDMOtpIMw6PyQhjZ8vCMUXeh7F7IlJEbIiFz2Lr8kfvikru008dN-lS2kkYT2xeA64LQE3x-FpaCeUDKv_TnHWaziuhPKND8xVo7Ce5o-f2zVpE"
MINIMAX_BASE_URL = "https://api.minimaxi.com/v1"


def generate_sql_via_minimax(user_input: str) -> Optional[str]:
    """通过 MiniMax API 生成 SQL"""
    try:
        prompt = SQL_GENERATOR_PROMPT.format(user_input=user_input)
        
        url = f"{MINIMAX_BASE_URL}/text/chatcompletion_v2"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MINIMAX_API_KEY}"
        }
        
        payload = {
            "model": "MiniMax-M2.1",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=60
        )
        
        print(f"MiniMax API response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # MiniMax 返回格式
            choices = data.get("choices", [])
            if choices:
                text = choices[0].get("message", {}).get("content", "")
                
                # 清理 SQL
                text = text.strip()
                if text.lower().startswith("```sql"):
                    text = text[6:]
                elif text.lower().startswith("```"):
                    text = text[3:]
                if text.lower().endswith("```"):
                    text = text[:-3]
                
                sql = text.strip()
                print(f"Generated SQL: {sql}")
                return sql
        else:
            print(f"API error: {response.text[:200]}")
            
    except Exception as e:
        print(f"MiniMax API error: {e}")
    
    return None


def generate_sql(user_input: str) -> Dict[str, Any]:
    """
    调用 LLM 生成 SQL
    """
    result = {
        "sql": None,
        "error": None
    }
    
    print(f"\n=== Generating SQL for: {user_input} ===")
    
    # 尝试通过 MiniMax API
    sql = generate_sql_via_minimax(user_input)
    if sql:
        result["sql"] = sql
        return result
    
    # 如果 LLM 失败，直接返回错误
    result["error"] = "LLM failed to generate SQL"
    
    return result


if __name__ == "__main__":
    # 测试
    test_input = "查询前5个物料的中文名称"
    print(f"Input: {test_input}")
    result = generate_sql(test_input)
    print(f"Result: {result}")

"""
LLM Service - SQL 生成服务
"""
import logging
import os
import requests
from typing import Dict, Any, Optional

from .config import DATABASE_SCHEMA

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMError(Exception):
    """LLM 调用异常"""
    pass


# Prompt 模板 - 使用动态 schema
SQL_GENERATOR_PROMPT = """你是一个专业SQL数据分析师。

已知表结构：
{schema_info}

规则：
1. 只允许生成 SELECT 查询
2. 禁止 DROP、DELETE、UPDATE、INSERT、ALTER、TRUNCATE
3. Trino SQL 跨库查询用 catalog.schema.table 格式
4. 字段名和别名只能用英文
5. 只返回SQL语句，不要任何解释

用户问题：{user_input}

只返回SQL。"""


# 校验 SQL 安全性
def basic_sql_validation(sql: str) -> bool:
    """
    基础 SQL 安全校验
    
    Returns:
        True: 通过校验
        False: 不通过
    """
    sql_lower = sql.lower()
    
    # 必须以 SELECT 开头
    if not sql_lower.startswith("select"):
        logger.warning(f"SQL does not start with SELECT: {sql[:50]}")
        return False
    
    # 禁止的关键词
    forbidden_keywords = [
        "drop", "delete", "update", "insert", "alter", "truncate",
        "create", "exec", "execute"
    ]
    for keyword in forbidden_keywords:
        if keyword in sql_lower:
            logger.warning(f"Forbidden keyword '{keyword}' found in SQL")
            return False
    
    # 禁止多语句
    if ";" in sql and sql.count(";") > 1:
        logger.warning("Multiple statements detected")
        return False
    
    return True


def clean_sql_output(text: str) -> str:
    """
    清理 LLM 输出的 SQL，去除 markdown 代码块标记
    """
    text = text.strip()
    
    # 去除 ```sql 或 ```
    if text.lower().startswith("```sql"):
        text = text[6:]
    elif text.lower().startswith("```"):
        text = text[3:]
    
    if text.lower().endswith("```"):
        text = text[:-3]
    
    return text.strip()


# API Key 检查
def get_api_key() -> str:
    """获取 API Key，环境变量优先"""
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        raise RuntimeError("MINIMAX_API_KEY not set in environment variables")
    return api_key


def generate_sql_via_minimax(user_input: str) -> Optional[str]:
    """通过 MiniMax API 生成 SQL"""
    # 获取 API Key
    api_key = get_api_key()
    
    # 构建 Prompt
    prompt = SQL_GENERATOR_PROMPT.format(
        schema_info=DATABASE_SCHEMA,
        user_input=user_input
    )
    
    url = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "MiniMax-M2.1",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0.1,
        "thinking": {"type": "disabled", "budget_tokens": 0}
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"MiniMax API response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            
            if choices:
                text = choices[0].get("message", {}).get("content", "")
                
                if not text:
                    logger.warning("LLM returned empty content")
                    raise LLMError("LLM returned empty content")
                
                sql = clean_sql_output(text)
                
                if not sql:
                    logger.warning("SQL is empty after cleaning")
                    raise LLMError("SQL is empty after cleaning")
                
                # 基础安全校验
                if not basic_sql_validation(sql):
                    raise LLMError("Generated SQL failed security validation")
                
                logger.info(f"Generated SQL: {sql[:100]}...")
                return sql
        else:
            logger.error(f"API error: {response.text[:200]}")
            raise LLMError(f"API returned {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        logger.exception("MiniMax API request failed")
        raise LLMError(f"Network error: {str(e)}")
    except LLMError:
        raise
    except Exception as e:
        logger.exception("Unexpected error in generate_sql_via_minimax")
        raise LLMError(str(e))
    
    return None


def generate_sql(user_input: str) -> Dict[str, Any]:
    """
    调用 LLM 生成 SQL
    
    Returns:
        {
            "sql": "...",  # 生成的 SQL
            "error": None   # 错误信息
        }
    """
    result = {
        "sql": None,
        "error": None
    }
    
    logger.info(f"Generating SQL for: {user_input}")
    
    try:
        sql = generate_sql_via_minimax(user_input)
        result["sql"] = sql
        
    except LLMError as e:
        result["error"] = str(e)
        logger.error(f"LLM error: {e}")
    except Exception as e:
        result["error"] = f"Internal error: {str(e)}"
        logger.exception("Unexpected error in generate_sql")
    
    return result


if __name__ == "__main__":
    # 测试
    test_input = "查询前5个物料"
    logger.info(f"Testing with input: {test_input}")
    result = generate_sql(test_input)
    logger.info(f"Result: {result}")

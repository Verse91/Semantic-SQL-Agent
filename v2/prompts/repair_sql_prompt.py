"""
SQL 修复 Prompt
"""


def build_repair_sql_prompt(
    original_sql: str,
    error_message: str,
    schema_context: str = ""
) -> str:
    """
    构建 SQL 修复 prompt
    
    Args:
        original_sql: 原始 SQL
        error_message: 错误信息
        schema_context: Schema 上下文
        
    Returns:
        prompt 字符串
    """
    prompt = f"""你是一个专业SQL数据分析师。

已知表结构：
{schema_context}

原始SQL：
{original_sql}

执行错误：
{error_message}

请修复上述 SQL，只返回修复后的 SQL 语句，不要任何解释。
修复规则：
1. 只允许 SELECT 查询
2. 检查表名、列名是否正确
3. 检查语法错误
4. 确保 SQL 可以正常执行

修复后的SQL："""
    
    return prompt

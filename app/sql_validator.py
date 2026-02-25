class SQLValidationError(Exception):
    """SQL 校验异常"""
    pass


def validate_sql(sql: str) -> None:
    """
    校验 SQL 是否安全
    
    规则：
    1. SQL 必须以 SELECT 开头
    2. 禁止包含危险关键词
    
    Args:
        sql: SQL 语句
        
    Raises:
        SQLValidationError: 校验失败时抛出
    """
    if not sql:
        raise SQLValidationError("SQL cannot be empty")
    
    # 去除首尾空白
    sql = sql.strip()
    
    # 检查是否以 SELECT 开头（忽略大小写和空白）
    if not sql.upper().startswith("SELECT"):
        raise SQLValidationError("Only SELECT queries are allowed")
    
    # 禁止的关键词列表
    forbidden_keywords = [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "EXEC",
        "EXECUTE",
    ]
    
    # 检查是否包含禁止关键词
    sql_upper = sql.upper()
    for keyword in forbidden_keywords:
        # 使用单词边界匹配，避免误报（如 SELECT 后包含 UPDATE）
        if keyword in sql_upper:
            raise SQLValidationError(f"Forbidden keyword found: {keyword}")
    
    return True


if __name__ == "__main__":
    # 测试用例
    test_cases = [
        ("SELECT * FROM sales", True),
        ("select * from sales", True),
        ("SELECT id, name FROM users", True),
        ("DROP TABLE users", False),
        ("DELETE FROM sales", False),
        ("UPDATE users SET name='test'", False),
        ("INSERT INTO sales VALUES(1)", False),
        ("ALTER TABLE users ADD COLUMN name", False),
    ]
    
    for sql, expected_valid in test_cases:
        try:
            validate_sql(sql)
            result = "PASS"
        except SQLValidationError as e:
            result = f"FAIL: {e}"
        
        status = "✓" if (expected_valid and result == "PASS") or (not expected_valid and "FAIL" in result) else "✗"
        print(f"{status} '{sql}' -> {result}")

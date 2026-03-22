"""
SQL Validator - 基于 AST 的 SQL 安全校验模块
"""
import logging
import sqlglot
from sqlglot import parse_one
from sqlglot.expressions import (
    Select, Insert, Update, Delete, Create, Drop, Alter,
    Into, ForIn, With, Subquery
)

logger = logging.getLogger(__name__)


class SQLValidationError(Exception):
    """SQL 校验异常"""
    pass


def validate_sql(sql: str, auto_limit: int = 1000) -> str:
    """
    校验 SQL 安全性
    
    基于 AST 的结构化校验：
    1. 语法解析
    2. 单语句检查
    3. 必须是 SELECT
    4. 禁止写操作节点
    5. 危险子句检查
    6. 自动追加 LIMIT
    
    Args:
        sql: 原始 SQL
        auto_limit: 自动追加的 LIMIT 值，默认 1000
        
    Returns:
        安全处理后的 SQL
    """
    if not sql or not sql.strip():
        raise SQLValidationError("SQL cannot be empty")
    
    sql = sql.strip()
    
    # Step 1: 语法解析
    try:
        tree = parse_one(sql)
    except Exception as e:
        logger.error(f"SQL syntax parse error: {e}")
        raise SQLValidationError(f"Invalid SQL syntax: {e}")
    
    # Step 2: 禁止多语句
    statements = sqlglot.parse(sql)
    if len(statements) != 1:
        raise SQLValidationError("Multiple statements are not allowed")
    
    # Step 3: 必须是 SELECT (允许 CTE + SELECT)
    if not isinstance(tree, Select):
        # 检查是否是 WITH (CTE) 包裹的 SELECT
        if isinstance(tree, With):
            # CTE 的第一个表达式必须是 SELECT
            cte_expressions = list(tree.expressions)
            if not cte_expressions or not isinstance(cte_expressions[0], Select):
                raise SQLValidationError("Only SELECT statements are allowed")
        else:
            raise SQLValidationError("Only SELECT statements are allowed")
    
    # Step 4: 禁止写操作节点
    forbidden_types = (Insert, Update, Delete, Create, Drop, Alter)
    for node in tree.walk():
        if isinstance(node, forbidden_types):
            raise SQLValidationError(f"Forbidden statement: {type(node).__name__}")
    
    # Step 5: 危险子句检查
    # 5.1 禁止 SELECT INTO
    if tree.find(Into):
        raise SQLValidationError("SELECT INTO is not allowed")
    
    # 5.2 禁止 FOR UPDATE
    if tree.find(ForIn):
        raise SQLValidationError("FOR UPDATE is not allowed")
    
    # 5.3 禁止写入型 CTE
    with_clause = tree.args.get("with")
    if with_clause:
        for cte in with_clause.expressions:
            for node in cte.walk():
                if isinstance(node, (Insert, Update, Delete)):
                    raise SQLValidationError("Write operations inside CTE are not allowed")
    
    # Step 6: 自动追加 LIMIT（如果没有）
    if not tree.args.get("limit"):
        # 动态创建 LIMIT 节点
        limit_value = sqlglot.exp.Limit(
            expression=sqlglot.exp.Literal.number(auto_limit)
        )
        tree.set("limit", limit_value)
        logger.info(f"Auto-added LIMIT {auto_limit}")
    
    # 返回处理后的 SQL
    validated_sql = tree.sql()
    logger.info(f"SQL validated successfully: {validated_sql[:100]}...")
    
    return validated_sql


def basic_sql_validation(sql: str) -> bool:
    """
    简单的 SQL 校验（快速检查）
    
    用于 LLM 生成 SQL 后的快速校验
    """
    sql_lower = sql.lower().strip()
    
    # 必须以 SELECT 开头
    if not sql_lower.startswith("select"):
        return False
    
    # 禁止关键词
    forbidden = ["drop", "delete", "update", "insert", "alter", "truncate", "create"]
    for kw in forbidden:
        if kw in sql_lower:
            return False
    
    # 禁止多语句（简单检查）
    if ";" in sql and sql.count(";") > 1:
        return False
    
    return True


if __name__ == "__main__":
    # 测试
    test_cases = [
        # 合法
        ("SELECT * FROM users", True),
        ("SELECT a.id, b.name FROM a JOIN b ON a.id = b.id", True),
        ("WITH cte AS (SELECT * FROM a) SELECT * FROM cte", True),
        ("SELECT region, COUNT(*) FROM sales GROUP BY region", True),
        
        # 非法
        ("DROP TABLE users", False),
        ("DELETE FROM users", False),
        ("UPDATE users SET name='test'", False),
        ("INSERT INTO users VALUES(1)", False),
        ("SELECT * FROM a; SELECT * FROM b", False),
    ]
    
    for sql, should_pass in test_cases:
        try:
            result = validate_sql(sql)
            passed = True
        except SQLValidationError as e:
            passed = False
            result = str(e)
        
        status = "✓" if passed == should_pass else "✗"
        print(f"{status} '{sql[:40]}...' -> {result[:50] if passed else result}")

import trino
import re
from typing import List, Dict, Any, Optional
from .config import TRINO_HOST, TRINO_PORT, TRINO_USER, TRINO_CATALOG, TRINO_SCHEMA


class TrinoError(Exception):
    """Trino 执行异常"""
    pass


def normalize_sql(sql: str) -> str:
    """
    规范化 SQL，转换为 Trino 兼容语法
    """
    # 去除首尾空白
    sql = sql.strip()
    
    # 去除末尾分号
    if sql.endswith(';'):
        sql = sql[:-1]
    
    # 转换 TOP 为 LIMIT
    # SELECT TOP N ... -> SELECT ... LIMIT N
    sql = re.sub(r'SELECT\s+TOP\s+(\d+)\s+(.*)$', r'SELECT \2 LIMIT \1', sql, flags=re.IGNORECASE | re.DOTALL)
    
    # 转换 TOP(*) 为 LIMIT
    sql = re.sub(r'SELECT\s+TOP\s+(\d+)\s+\*', r'SELECT * LIMIT \1', sql, flags=re.IGNORECASE)
    
    return sql.strip()


def get_trino_connection():
    """建立 Trino 连接"""
    try:
        conn = trino.dbapi.connect(
            host=TRINO_HOST,
            port=int(TRINO_PORT),
            user=TRINO_USER,
            catalog=TRINO_CATALOG,
            schema=TRINO_SCHEMA,
        )
        return conn
    except Exception as e:
        raise TrinoError(f"Failed to connect to Trino: {str(e)}")


def execute_query(sql: str) -> Dict[str, Any]:
    """
    执行 SQL 查询并返回 JSON 格式结果
    
    Args:
        sql: SELECT 查询语句
        
    Returns:
        {
            "data": [...],  # 查询结果
            "error": None   # 错误信息，无错误时为 None
        }
    """
    result = {
        "data": None,
        "error": None
    }
    
    conn = None
    cursor = None
    
    try:
        # 规范化 SQL
        sql = normalize_sql(sql)
        
        conn = get_trino_connection()
        cursor = conn.cursor()
        
        # 执行查询
        cursor.execute(sql)
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # 获取所有结果
        rows = cursor.fetchall()
        
        # 转换为字典列表
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            data.append(row_dict)
        
        result["data"] = data
        
    except Exception as e:
        result["error"] = str(e)
        
    finally:
        # 关闭连接
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    return result


if __name__ == "__main__":
    # 测试连接
    test_sql = "SELECT * FROM mara LIMIT 5"
    print(f"Executing: {test_sql}")
    result = execute_query(test_sql)
    print(f"Result: {result}")

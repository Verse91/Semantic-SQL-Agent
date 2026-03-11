"""
Trino 执行器
复用现有的 trino_service
"""
import os
import sys

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, '..'))

from app.trino_service import execute_query as trino_execute_query


class TrinoExecutor:
    """Trino 执行器"""
    
    def __init__(self):
        pass
    
    def execute(self, sql: str) -> dict:
        """
        执行 SQL
        
        Args:
            sql: SQL 查询
            
        Returns:
            结果字典
        """
        # 自动追加 LIMIT
        sql_upper = sql.upper()
        if "LIMIT" not in sql_upper:
            sql = f"{sql} LIMIT 1000"
        
        result = trino_execute_query(sql)
        
        if result.get("error"):
            raise Exception(result["error"])
        
        data = result.get("data", [])
        
        # 提取列名
        columns = []
        if data:
            columns = list(data[0].keys())
        
        # 转换为行数组
        rows = []
        for row in data:
            rows.append(list(row.values()))
        
        return {
            "data": data,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows)
        }

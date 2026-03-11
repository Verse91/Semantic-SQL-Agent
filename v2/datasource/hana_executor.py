"""
HANA 执行器
复用现有的 hana_executor
"""
import os
import sys

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, '..'))

from app.datasource.hana_executor import HanaExecutor as OriginalHanaExecutor


class HanaExecutor:
    """HANA 执行器"""
    
    def __init__(self):
        self._executor = OriginalHanaExecutor("config/database.yaml")
    
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
        
        data = self._executor.run_query(sql)
        
        # 提取列名
        columns = []
        if data:
            columns = list(data[0].keys()) if isinstance(data[0], dict) else []
        
        return {
            "data": data,
            "columns": columns,
            "rows": data,
            "row_count": len(data)
        }

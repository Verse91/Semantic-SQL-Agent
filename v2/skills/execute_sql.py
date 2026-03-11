"""
SQL 执行 Skill
"""
import os
import sys
import psycopg2
from typing import Dict, Any
from skills.base import BaseSkill

# 添加父项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


class ExecuteSQLSkill(BaseSkill):
    """SQL 执行 Skill"""
    
    name = "execute_sql"
    description = "根据数据源执行 SQL 查询"
    
    def __init__(self):
        self.pg_conn = None
    
    def _get_pg_connection(self):
        """获取 PostgreSQL 连接"""
        if self.pg_conn is None or self.pg_conn.closed:
            self.pg_conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="sap_mock",
                user="postgres",
                password="postgres"
            )
        return self.pg_conn
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行 SQL"""
        sql = state.get("validated_sql", "")
        datasource = state.get("datasource", "postgresql")
        
        if not sql:
            state["error"] = "No SQL to execute"
            return state
        
        try:
            conn = self._get_pg_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # 如果是 SELECT 查询，获取结果
            if sql.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
            else:
                conn.commit()
                data = []
                columns = []
                rows = []
            
            cursor.close()
            
            result = {
                "data": data,
                "columns": columns,
                "rows": rows,
                "row_count": len(data)
            }
            
            state["execution_result"] = result
            state["error"] = None
            
        except Exception as e:
            state["execution_result"] = None
            state["error"] = str(e)
        
        return state


# 实例
execute_sql_skill = ExecuteSQLSkill()

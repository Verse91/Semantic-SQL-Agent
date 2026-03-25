"""
SQL 执行 Skill
"""
import os
import sys
import psycopg2
from psycopg2 import pool
from typing import Dict, Any
from skills.base import BaseSkill
import logging
import time

# 添加父项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入 trace 模块
try:
    from tracing import log_execute_sql
    HAS_TRACING = True
except ImportError:
    HAS_TRACING = False

logger = logging.getLogger(__name__)


class ExecuteSQLSkill(BaseSkill):
    """SQL 执行 Skill"""
    
    name = "execute_sql"
    description = "根据数据源执行 SQL 查询"
    
    def __init__(self):
        # 使用连接池
        self.pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            host="localhost",
            port=5432,
            database="sap_mock",
            user="postgres",
            password="postgres"
        )
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行 SQL"""
        sql = state.get("validated_sql", "")
        datasource = state.get("datasource", "postgresql")
        start_time = time.time()
        
        if not sql:
            state["error"] = "No SQL to execute"
            return state
        
        conn = None
        try:
            # 从池中获取连接
            conn = self.pool.getconn()
            conn.set_session(autocommit=True)  # 设置自动提交
            cursor = conn.cursor()
            
            logger.info(f"Executing SQL: {sql[:100]}...")
            cursor.execute(sql)
            
            # 如果是 SELECT 查询，获取结果
            if sql.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
            else:
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
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            state["execution_result"] = result
            state["error"] = None
            logger.info(f"Query successful: {len(data)} rows, {execution_time_ms:.2f}ms")
            
            # Trace logging
            if HAS_TRACING:
                log_execute_sql(sql, len(data), execution_time_ms, None)
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"SQL Error: {e}")
            state["execution_result"] = None
            state["error"] = str(e)
            
            # Trace logging
            if HAS_TRACING:
                log_execute_sql(sql, 0, execution_time_ms, str(e))
        
        finally:
            # 归还连接到池
            if conn:
                self.pool.putconn(conn)
        
        return state


# 工厂函数
def get_execute_sql_skill() -> ExecuteSQLSkill:
    """获取 ExecuteSQLSkill 实例（工厂函数，避免单例问题）"""
    return ExecuteSQLSkill()


# 实例（保留向后兼容）
execute_sql_skill = ExecuteSQLSkill()

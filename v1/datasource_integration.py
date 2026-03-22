"""
带路由的 SQL 执行服务
示例：展示如何将 QueryRouter 集成到现有架构

使用方式:
1. 安装依赖: pip install jaydebeapi JPype1
2. 放入 JDBC 驱动: drivers/ngdbc.jar
3. 配置: config/database.yaml
4. 取消下面的注释来启用路由
"""

# from .datasource import get_router
# from . import trino_service


# class RouterExecuteMixin:
#     """Mixin to add routing capability to execute_sql"""
    
#     def __#         selfinit__(self):
.router = get_router()
#         # 设置默认执行器为 Trino
#         self.router.set_default_executor(trino_service)
    
#     def execute_sql(self, sql: str):
#         """
#         通过路由执行 SQL
        
#         Args:
#             sql: SELECT 查询语句
            
#         Returns:
#             {
#                 "data": [...],
#                 "error": None
#             }
#         """
#         try:
#             # 路由执行
#             data = self.router.execute(sql)
#             return {
#                 "data": data,
#                 "error": None
#             }
#         except Exception as e:
#             return {
#                 "data": None,
#                 "error": str(e)
#             }


# ============================================================
# 集成到 API 路由的示例 (修改 app/api/routes.py)
# ============================================================

"""
在 routes.py 中替换 execute_sql 函数:

# 方式 1: 导入并使用
from app.datasource import get_router
from app import trino_service

router = get_router()
router.set_default_executor(trino_service)

@router.post("/execute_sql")
async def execute_sql(request: ExecuteSQLRequest):
    # ... 前面的验证代码保持不变 ...
    
    # 执行 SQL (通过路由器)
    start_time = time.time()
    try:
        data = router.execute(sql)
        execution_time = int((time.time() - start_time) * 1000)
        
        # 格式化返回
        columns = list(data[0].keys()) if data else []
        rows = [list(row.values()) for row in data]
        
        result["success"] = True
        result["data"] = {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": execution_time
        }
    except Exception as e:
        result["error"] = f"Query Error: {str(e)}"

# 方式 2: 创建包装函数
def execute_with_router(sql: str):
    '''通过路由器执行查询'''
    return router.execute(sql)

# 方式 3: 直接使用
from app.datasource import HanaExecutor, QueryRouter

# 只执行 HANA 查询
hana = HanaExecutor()
result = hana.run_query("SELECT * FROM MARA LIMIT 10")
"""

# ============================================================
# 依赖安装
# ============================================================

"""
# 安装 Python 依赖
pip install jaydebeapi JPype1

# 或使用项目虚拟环境
cd Semantic-SQL-Agent
source venv/bin/activate
pip install jaydebeapi JPype1
"""

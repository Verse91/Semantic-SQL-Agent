import time
from fastapi import APIRouter, HTTPException
from ..models.request_models import GenerateSQLRequest, ExecuteSQLRequest
from ..llm_service import generate_sql as llm_generate_sql
from ..sql_validator import validate_sql, SQLValidationError
from ..trino_service import execute_query as trino_execute_query
from ..datasource import get_router

# Trino 适配器 - 将 Trino 返回格式转为 Router 期望的格式
class TrinoAdapter:
    """Trino 适配器，用于 QueryRouter"""
    
    @staticmethod
    def run_query(sql: str):
        """
        执行查询并转换为 Router 期望的格式
        
        Router 期望: List[Dict]
        Trino 返回: {"data": [...], "error": None}
        """
        result = trino_execute_query(sql)
        if result.get("error"):
            raise Exception(result["error"])
        return result.get("data", [])


# 初始化查询路由器
query_router = get_router()

# 设置默认执行器为 Trino
query_router.set_default_executor(TrinoAdapter())

router = APIRouter()


@router.post("/generate_sql")
async def generate_sql(request: GenerateSQLRequest):
    """
    生成 SQL - 接收自然语言，调用 LLM 生成 SQL
    """
    result = {
        "success": False,
        "data": None,
        "error": None
    }
    
    try:
        # 调用 LLM 生成 SQL
        llm_result = llm_generate_sql(request.question)
        
        if llm_result.get("error"):
            result["error"] = f"LLM Error: {llm_result['error']}"
            return result
        
        sql = llm_result.get("sql")
        if not sql:
            result["error"] = "Failed to generate SQL"
            return result
        
        # SQL 安全校验
        try:
            validate_sql(sql)
        except SQLValidationError as e:
            result["error"] = f"SQL validation failed: {str(e)}"
            return result
        
        result["success"] = True
        result["data"] = {
            "sql": sql
        }
        
    except Exception as e:
        result["error"] = f"Internal error: {str(e)}"
    
    return result


@router.post("/execute_sql")
async def execute_sql(request: ExecuteSQLRequest):
    """
    执行 SQL - 接收 SQL，执行并返回结果
    支持 SAP 表查询 (路由到 HANA) 和其他查询 (路由到 Trino)
    """
    result = {
        "success": False,
        "data": None,
        "error": None
    }
    
    try:
        sql = request.sql.strip()
        
        if not sql:
            result["error"] = "SQL cannot be empty"
            return result
        
        # SQL 安全校验 (原有校验)
        try:
            validate_sql(sql)
        except SQLValidationError as e:
            result["error"] = f"SQL validation failed: {str(e)}"
            return result
        
        # 检查是否包含分号（禁止多语句）
        if ';' in sql and sql.count(';') > 1:
            result["error"] = "Multiple statements are not allowed"
            return result
        
        # 自动追加 LIMIT（如果没有）
        sql_upper = sql.upper()
        if 'LIMIT' not in sql_upper:
            sql = f"{sql} LIMIT 1000"
        
        # 执行 SQL - 通过路由器自动选择数据源
        start_time = time.time()
        
        try:
            # 使用路由器执行（会自动路由到 HANA 或 Trino）
            query_result = query_router.execute(sql)
            execution_time = int((time.time() - start_time) * 1000)
            
            if query_result.get("error"):
                result["error"] = query_result["error"]
                return result
            
            data = query_result.get("data", [])
            
        except Exception as e:
            # 如果路由器执行失败，回退到原有的 Trino 执行
            # 这确保了向后兼容性
            trino_result = trino_execute_query(sql)
            execution_time = int((time.time() - start_time) * 1000)
            
            if trino_result.get("error"):
                result["error"] = f"Trino Error: {trino_result['error']}"
                return result
            
            data = trino_result.get("data", [])
        
        # 提取列名
        columns = []
        if data:
            columns = list(data[0].keys())
        
        # 转换为行数组
        rows = []
        for row in data:
            rows.append(list(row.values()))
        
        result["success"] = True
        result["data"] = {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_time_ms": execution_time
        }
        
    except Exception as e:
        result["error"] = f"Internal error: {str(e)}"
    
    return result

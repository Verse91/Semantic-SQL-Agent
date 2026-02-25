from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from .llm_service import generate_sql, LLMError
from .sql_validator import validate_sql, SQLValidationError
from .trino_service import execute_query, TrinoError

app = FastAPI(
    title="AI SQL Agent",
    description="自然语言转 Trino SQL 查询服务",
    version="1.0.0"
)


# 请求模型
class ChatQueryRequest(BaseModel):
    message: str


# 响应模型
class ChatQueryResponse(BaseModel):
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


@app.get("/")
def root():
    """健康检查"""
    return {
        "status": "ok",
        "service": "AI SQL Agent",
        "version": "1.0.0"
    }


@app.post("/chat-query", response_model=ChatQueryResponse)
def chat_query(request: ChatQueryRequest):
    """
    处理自然语言查询请求
    
    流程：
    1. 接收自然语言
    2. 调用 LLM 生成 SQL
    3. 校验 SQL 安全性
    4. 执行 SQL
    5. 返回结果
    """
    response = ChatQueryResponse()
    
    try:
        # Step 1: 调用 LLM 生成 SQL
        llm_result = generate_sql(request.message)
        
        if llm_result.get("error"):
            response.error = f"LLM Error: {llm_result['error']}"
            return response
        
        sql = llm_result.get("sql")
        if not sql:
            response.error = "Failed to generate SQL"
            return response
        
        # Step 2: 校验 SQL
        try:
            validate_sql(sql)
        except SQLValidationError as e:
            response.sql = sql
            response.error = f"SQL validation failed: {str(e)}"
            return response
        
        # Step 3: 执行 SQL
        trino_result = execute_query(sql)
        
        response.sql = sql
        
        if trino_result.get("error"):
            response.error = f"Trino Error: {trino_result['error']}"
        else:
            response.data = trino_result.get("data", [])
            
    except Exception as e:
        response.error = f"Internal error: {str(e)}"
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

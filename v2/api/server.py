"""
FastAPI Server
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import warnings
# 忽略 Pydantic V1 兼容性警告 (Python 3.14 兼容性问题)
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.v1")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uuid

from agent.graph import workflow
from memory.conversation_memory import get_conversation_memory
from memory.session_store import get_session_store

app = FastAPI(
    title="Semantic-SQL-Agent V2",
    description="Data Agent with LangGraph",
    version="2.0.0"
)

# 添加 CORS 支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求模型
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    query: str


# 响应模型
class ChatResponse(BaseModel):
    session_id: str
    sql: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


@app.get("/")
def root():
    """健康检查"""
    return {
        "status": "ok",
        "service": "Semantic-SQL-Agent V2",
        "version": "2.0.0"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """处理对话请求"""
    # 获取或创建会话
    session_store = get_session_store()
    memory = get_conversation_memory()
    
    if request.session_id:
        session_id = request.session_id
        # 检查会话是否存在
        if not session_store.get(session_id):
            session_id = session_store.create(session_id)
    else:
        session_id = session_store.create()
    
    try:
        # 获取对话历史
        history = memory.get_recent(session_id, count=4)
        
        # 构建初始状态
        initial_state = {
            "user_query": request.query,
            "conversation_history": history,
            "schema_context": "",
            "generated_sql": "",
            "validated_sql": "",
            "datasource": "trino",
            "execution_result": None,
            "error": None,
            "retry_count": 0
        }
        
        # 执行工作流
        result = workflow.invoke(initial_state)
        
        # 保存对话
        if result.get("validated_sql"):
            memory.add(session_id, "user", request.query)
            memory.add(session_id, "assistant", result["validated_sql"])
        
        # 更新会话
        session_store.update(session_id, {
            "last_query": request.query,
            "last_sql": result.get("validated_sql", "")
        })
        
        return ChatResponse(
            session_id=session_id,
            sql=result.get("validated_sql"),
            result=result.get("execution_result"),
            error=result.get("error")
        )
        
    except Exception as e:
        return ChatResponse(
            session_id=session_id,
            error=str(e)
        )


# ========== V1 兼容 API ==========

class GenerateSQLRequest(BaseModel):
    question: str


@app.post("/api/generate_sql")
async def generate_sql(request: GenerateSQLRequest):
    """V1 兼容: 生成 SQL"""
    from skills.generate_sql import generate_sql_skill
    from schema.schema_retriever import retrieve_schema
    
    try:
        # 获取 schema
        schema = retrieve_schema(request.question)
        
        # 构建状态
        state = {
            "user_query": request.question,
            "conversation_history": [],
            "schema_context": schema,
            "generated_sql": "",
            "validated_sql": "",
            "datasource": "postgresql",
            "execution_result": None,
            "error": None,
            "retry_count": 0
        }
        
        # 生成 SQL
        state = generate_sql_skill.run(state)
        
        return {
            "success": state.get("error") is None,
            "data": {"sql": state.get("generated_sql", "")},
            "error": state.get("error")
        }
    except Exception as e:
        return {"success": False, "data": {"sql": None}, "error": str(e)}


class ExecuteSQLRequest(BaseModel):
    sql: str


@app.post("/api/execute_sql")
async def execute_sql(request: ExecuteSQLRequest):
    """V1 兼容: 执行 SQL"""
    from skills.execute_sql import execute_sql_skill
    
    try:
        state = {
            "user_query": "",
            "conversation_history": [],
            "schema_context": "",
            "generated_sql": request.sql,
            "validated_sql": request.sql,
            "datasource": "postgresql",
            "execution_result": None,
            "error": None,
            "retry_count": 0
        }
        
        state = execute_sql_skill.run(state)
        
        return {
            "success": state.get("error") is None,
            "data": state.get("execution_result", {}),
            "error": state.get("error")
        }
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


@app.get("/session/{session_id}/history")
def get_history(session_id: str):
    """获取会话历史"""
    memory = get_conversation_memory()
    history = memory.get(session_id)
    return {"session_id": session_id, "history": history}


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    """删除会话"""
    memory = get_conversation_memory()
    session_store = get_session_store()
    
    memory.clear(session_id)
    session_store.delete(session_id)
    
    return {"status": "deleted", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

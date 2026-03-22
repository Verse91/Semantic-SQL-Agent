"""
FastAPI Server
"""
import os
import sys

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

from memory.conversation_memory import get_conversation_memory
from memory.session_store import get_session_store

# 导入 trace 模块
try:
    from tracing import start_trace, end_trace
    # 预加载 skills 以确保模块实例一致
    from skills.generate_sql import generate_sql_skill
    from skills.validate_sql import validate_sql_skill
    from skills.route_datasource import route_datasource_skill
    from skills.execute_sql import execute_sql_skill
    from skills.format_result import format_result_skill
    from schema.schema_retriever import retrieve_schema
    HAS_TRACING = True
except ImportError:
    HAS_TRACING = False

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
        # 开始 Trace
        if HAS_TRACING:
            start_trace(request.query, session_id)
        
        # 获取对话历史
        history = memory.get_recent(session_id, count=4)
        
        # 直接调用 skills (绕过 LangGraph 避免并发问题)
        from skills.generate_sql import generate_sql_skill
        from skills.validate_sql import validate_sql_skill
        from skills.route_datasource import route_datasource_skill
        from skills.execute_sql import execute_sql_skill
        from skills.format_result import format_result_skill
        from schema.schema_retriever import get_schema_retriever
        
        # 1. 获取 Schema (使用 retrieve_with_tables 获取表名列表)
        retriever = get_schema_retriever()
        schema_context, retrieved_tables = retriever.retrieve_with_tables(request.query)
        
        # 构建状态
        state = {
            "user_query": request.query,
            "conversation_history": history,
            "schema_context": schema_context,
            "retrieved_tables": retrieved_tables,
            "generated_sql": "",
            "validated_sql": "",
            "datasource": "postgresql",
            "execution_result": None,
            "error": None,
            "retry_count": 0
        }
        
        # 2. 生成 SQL
        state = generate_sql_skill.run(state)
        
        # 3. 校验 SQL
        if not state.get("error"):
            state = validate_sql_skill.run(state)
        
        # 4. 路由数据源
        if not state.get("error"):
            state = route_datasource_skill.run(state)
        
        # 5. 执行 SQL
        if not state.get("error"):
            state = execute_sql_skill.run(state)
        
        # 6. 格式化结果
        if not state.get("error"):
            state = format_result_skill.run(state)
        
        result = state
        
        # 保存对话
        if result.get("validated_sql"):
            memory.add(session_id, "user", request.query)
            memory.add(session_id, "assistant", result["validated_sql"])
        
        # 更新会话
        session_store.update(session_id, {
            "last_query": request.query,
            "last_sql": result.get("validated_sql", "")
        })
        
        # 结束 Trace (success)
        if HAS_TRACING:
            end_trace("success")
        
        return ChatResponse(
            session_id=session_id,
            sql=result.get("validated_sql"),
            result=result.get("execution_result"),
            error=result.get("error")
        )
        
    except Exception as e:
        # 结束 Trace (failed)
        if HAS_TRACING:
            end_trace("failed")
        
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
    from schema.schema_retriever import get_schema_retriever
    
    try:
        # 获取 schema 和表名列表
        retriever = get_schema_retriever()
        schema, retrieved_tables = retriever.retrieve_with_tables(request.question)
        
        # 构建状态
        state = {
            "user_query": request.question,
            "conversation_history": [],
            "schema_context": schema,
            "retrieved_tables": retrieved_tables,
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


# ========== FS 报表上传接口 ==========

from fastapi import UploadFile, File
import tempfile
from documents.fs_loader import get_fs_loader


@app.post("/api/upload_fs")
async def upload_fs(
    file: UploadFile = File(...),
    session_id: Optional[str] = None
):
    """上传 FS 报表文档并执行"""
    try:
        # 1. 保存上传的文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # 2. 加载 FS 文档
        loader = get_fs_loader()
        fs_document = loader.load(tmp_path)
        
        # 清理临时文件
        os.unlink(tmp_path)
        
        # 3. 解析 FS
        from skills.parse_fs import parse_fs_skill
        state = {
            "user_query": "",
            "fs_document": fs_document,
            "fs_json": {},
            "query_plan": {},
            "schema_context": "",
            "generated_sql": "",
            "validated_sql": "",
            "datasource": "postgresql",
            "execution_result": None,
            "error": None,
            "retry_count": 0,
            "conversation_history": [],
            "session_id": session_id or str(uuid.uuid4()),
            "mode": "fs"
        }
        
        # 4. 解析 FS
        state = parse_fs_skill.run(state)
        if state.get("error"):
            return {"success": False, "error": f"FS解析失败: {state['error']}"}
        
        # 5. 获取 Schema (使用 retrieve_with_tables 获取表名列表)
        from schema.schema_retriever import get_schema_retriever
        retriever = get_schema_retriever()
        state["schema_context"], state["retrieved_tables"] = retriever.retrieve_with_tables("")
        
        # 6. 生成 Query Plan
        from skills.generate_query_plan import generate_query_plan_skill
        state = generate_query_plan_skill.run(state)
        if state.get("error"):
            return {"success": False, "error": f"Query Plan生成失败: {state['error']}"}
        
        # 7. 生成 SQL
        from skills.generate_sql import generate_sql_skill
        state = generate_sql_skill.run(state)
        if state.get("error"):
            return {"success": False, "error": f"SQL生成失败: {state['error']}"}
        
        # 8. 校验 SQL
        from skills.validate_sql import validate_sql_skill
        state = validate_sql_skill.run(state)
        if state.get("error"):
            return {"success": False, "error": f"SQL校验失败: {state['error']}"}
        
        # 9. 路由数据源
        from skills.route_datasource import route_datasource_skill
        state = route_datasource_skill.run(state)
        
        # 10. 执行 SQL
        from skills.execute_sql import execute_sql_skill
        state = execute_sql_skill.run(state)
        if state.get("error"):
            return {"success": False, "error": f"SQL执行失败: {state['error']}"}
        
        # 11. 格式化结果
        from skills.format_result import format_result_skill
        state = format_result_skill.run(state)
        
        return {
            "success": True,
            "session_id": state["session_id"],
            "fs_json": state.get("fs_json"),
            "query_plan": state.get("query_plan"),
            "sql": state.get("validated_sql"),
            "result": state.get("execution_result"),
            "error": state.get("error")
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========== Trace API ==========

@app.get("/api/traces")
def list_traces(date: str = None, limit: int = 50):
    """列出历史 Traces"""
    try:
        from tracing import get_storage
        storage = get_storage()
        traces = storage.list_traces(date, limit)
        return {"traces": traces}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/traces/{trace_id}")
def get_trace(trace_id: str, date: str = None):
    """获取单条 Trace"""
    try:
        from tracing import get_storage
        storage = get_storage()
        trace = storage.get(trace_id, date)
        if trace:
            return trace
        return {"error": "Trace not found"}
    except Exception as e:
        return {"error": str(e)}

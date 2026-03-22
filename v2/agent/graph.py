"""
LangGraph Workflow 定义 (支持 FS 模式)
"""
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from langgraph.graph import StateGraph, END
from .state import AgentState


def create_workflow() -> StateGraph:
    """
    创建 Agent Workflow (支持两种模式)
    
    模式1 - 普通查询:
    retrieve_schema → generate_sql → validate_sql → 
    route_datasource → execute_sql → format_result
    
    模式2 - FS报表:
    load_fs → parse_fs → schema_retrieval → generate_query_plan → 
    generate_sql → validate_sql → route_datasource → execute_sql → format_result
    """
    workflow = StateGraph(AgentState)
    
    # 添加所有节点
    workflow.add_node("route_decision", route_decision_node)
    workflow.add_node("retrieve_schema", retrieve_schema_node)
    workflow.add_node("load_fs", load_fs_node)
    workflow.add_node("parse_fs", parse_fs_node)
    workflow.add_node("generate_query_plan", generate_query_plan_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("route_datasource", route_datasource_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("format_result", format_result_node)
    
    # 设置入口点
    workflow.set_entry_point("route_decision")
    
    # 路由决策节点 - 判断是普通查询还是 FS 模式
    workflow.add_conditional_edges(
        "route_decision",
        decide_mode,
        {
            "query": "retrieve_schema",
            "fs": "load_fs"
        }
    )
    
    # 普通查询流程
    workflow.add_edge("retrieve_schema", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")
    workflow.add_edge("validate_sql", "route_datasource")
    workflow.add_edge("route_datasource", "execute_sql")
    
    # FS 模式流程
    workflow.add_edge("load_fs", "parse_fs")
    workflow.add_edge("parse_fs", "retrieve_schema")
    workflow.add_edge("retrieve_schema", "generate_query_plan")
    workflow.add_edge("generate_query_plan", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")
    workflow.add_edge("validate_sql", "route_datasource")
    workflow.add_edge("route_datasource", "execute_sql")
    
    # 执行结果分支
    workflow.add_conditional_edges(
        "execute_sql",
        should_retry,
        {
            "success": "format_result",
            "retry": "execute_sql"  # 错误时重试当前节点
        }
    )
    
    # 完成
    workflow.add_edge("format_result", END)
    
    return workflow


# ========== 节点函数 ==========

def route_decision_node(state: AgentState) -> AgentState:
    """路由决策节点"""
    # 如果有 fs_document，进入 FS 模式
    if state.get("fs_document"):
        state["mode"] = "fs"
    else:
        state["mode"] = "query"
    return state


def decide_mode(state: AgentState) -> str:
    """判断模式"""
    return state.get("mode", "query")


def retrieve_schema_node(state: AgentState) -> AgentState:
    """Schema 检索节点"""
    from schema.schema_retriever import get_schema_retriever
    retriever = get_schema_retriever()
    schema_context, retrieved_tables = retriever.retrieve_with_tables(state["user_query"])
    state["schema_context"] = schema_context
    state["retrieved_tables"] = retrieved_tables
    return state


def load_fs_node(state: AgentState) -> AgentState:
    """加载 FS 文档"""
    # fs_document 已经在 state 中
    return state


def parse_fs_node(state: AgentState) -> AgentState:
    """解析 FS 节点"""
    from skills.parse_fs import parse_fs_skill
    return parse_fs_skill.run(state)


def generate_query_plan_node(state: AgentState) -> AgentState:
    """生成 Query Plan 节点"""
    from skills.generate_query_plan import generate_query_plan_skill
    return generate_query_plan_skill.run(state)


def generate_sql_node(state: AgentState) -> AgentState:
    """SQL 生成节点"""
    from skills.generate_sql import generate_sql_skill
    return generate_sql_skill.run(state)


def validate_sql_node(state: AgentState) -> AgentState:
    """SQL 校验节点"""
    from skills.validate_sql import validate_sql_skill
    return validate_sql_skill.run(state)


def route_datasource_node(state: AgentState) -> AgentState:
    """数据源路由节点"""
    from skills.route_datasource import route_datasource_skill
    return route_datasource_skill.run(state)


def execute_sql_node(state: AgentState) -> AgentState:
    """SQL 执行节点"""
    from skills.execute_sql import execute_sql_skill
    return execute_sql_skill.run(state)


def format_result_node(state: AgentState) -> AgentState:
    """结果格式化节点"""
    from skills.format_result import format_result_skill
    return format_result_skill.run(state)


# ========== 条件函数 ==========

def should_retry(state: AgentState) -> str:
    """
    判断是否需要重试
    
    Returns:
        "success" 或 "retry"
    """
    error = state.get("error")
    retry_count = state.get("retry_count", 0)
    
    if error and retry_count < 2:
        state["retry_count"] = retry_count + 1
        return "retry"
    return "success"


# ========== 编译 ==========

def compile_workflow():
    """编译工作流"""
    workflow = create_workflow()
    return workflow.compile()


# 默认工作流实例
workflow = compile_workflow()

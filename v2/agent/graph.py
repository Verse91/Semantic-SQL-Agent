"""
LangGraph Workflow 定义
"""
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from langgraph.graph import StateGraph, END
from .state import AgentState


def create_workflow() -> StateGraph:
    """
    创建 Agent Workflow (简化版)
    
    流程:
    retrieve_schema → generate_sql → validate_sql → 
    route_datasource → execute_sql → format_result
    """
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("retrieve_schema", retrieve_schema_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("validate_sql", validate_sql_node)
    workflow.add_node("route_datasource", route_datasource_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("format_result", format_result_node)
    
   
    workflow.set_entry_point("retrieve_schema")
    
    # 添加边
    workflow.add_edge("retrieve_schema", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")
    workflow.add_edge("validate_sql", "route_datasource")
    workflow.add_edge("route_datasource", "execute_sql")
    workflow.add_edge("execute_sql", "format_result")
    workflow.add_edge("format_result", END)
    
    return workflow


# ========== 节点函数 ==========

def retrieve_schema_node(state: AgentState) -> AgentState:
    """Schema 检索节点"""
    from schema.schema_retriever import retrieve_schema
    schema_context = retrieve_schema(state["user_query"])
    state["schema_context"] = schema_context
    return state


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


# ========== 编译 ==========

def compile_workflow():
    """编译工作流"""
    workflow = create_workflow()
    return workflow.compile()


# 默认工作流实例
workflow = compile_workflow()

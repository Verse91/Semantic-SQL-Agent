"""
LangGraph Workflow 定义 (支持 FS 模式)
"""
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from langgraph.graph import StateGraph, END
from .state import AgentState

# 导入 trace 模块
try:
    from tracing import log_step, log_schema_retriever, log_generate_sql
    from tracing import log_validate_sql, log_execute_sql, log_repair_sql
    from tracing import log_route_datasource
    HAS_TRACING = True
except ImportError:
    HAS_TRACING = False


def create_workflow() -> StateGraph:
    """
    创建 Agent Workflow (支持两种模式)

    模式1 - 普通查询:
    retrieve_schema → generate_sql → validate_sql →
    route_datasource → execute_sql → format_result

    模式2 - FS报表:
    load_fs → parse_fs → schema_retrieval → generate_query_plan →
    generate_sql → validate_sql → route_datasource → execute_sql → format_result

    重试流程:
    execute_sql → (失败) → repair_sql → execute_sql
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
    workflow.add_node("repair_sql", repair_sql_node)
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
    workflow.add_edge("generate_sql", "validate_sql")
    workflow.add_edge("validate_sql", "route_datasource")
    workflow.add_edge("route_datasource", "execute_sql")

    # FS 模式流程
    workflow.add_edge("load_fs", "parse_fs")
    workflow.add_edge("parse_fs", "retrieve_schema")
    workflow.add_edge("generate_query_plan", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")
    workflow.add_edge("validate_sql", "route_datasource")
    workflow.add_edge("route_datasource", "execute_sql")

    # retrieve_schema 根据 mode 条件路由（query 模式到 generate_sql，FS 模式到 generate_query_plan）
    workflow.add_conditional_edges(
        "retrieve_schema",
        lambda s: s.get("mode", "query"),
        {
            "query": "generate_sql",
            "fs": "generate_query_plan"
        }
    )
    
    # 执行结果分支
    workflow.add_conditional_edges(
        "execute_sql",
        should_retry,
        {
            "success": "format_result",
            "retry": "repair_sql"  # 错误时修复 SQL
        }
    )

    # 修复后重新执行
    workflow.add_edge("repair_sql", "execute_sql")

    # 完成
    workflow.add_edge("format_result", END)
    
    return workflow


# ========== 节点函数 ==========

def route_decision_node(state: AgentState) -> dict:
    """路由决策节点 - 只返回需要更新的字段"""
    mode = "fs" if state.get("fs_document") else "query"
    return {"mode": mode}


def decide_mode(state: AgentState) -> str:
    """判断模式"""
    return state.get("mode", "query")


def retrieve_schema_node(state: AgentState) -> dict:
    """Schema 检索节点 - 只返回更新的字段"""
    from schema.schema_retriever import get_schema_retriever
    retriever = get_schema_retriever()
    schema_context, retrieved_tables = retriever.retrieve_with_tables(state["user_query"])

    # Trace logging
    if HAS_TRACING:
        log_schema_retriever(state["user_query"], retrieved_tables)

    return {"schema_context": schema_context, "retrieved_tables": retrieved_tables}


def load_fs_node(state: AgentState) -> dict:
    """加载 FS 文档 - 无需更新任何字段"""
    return {}


def parse_fs_node(state: AgentState) -> dict:
    """解析 FS 节点"""
    from skills.parse_fs import parse_fs_skill
    state = parse_fs_skill.run(state)

    # Trace logging
    if HAS_TRACING:
        log_step("parse_fs", input_data={"fs_document": state.get("fs_document", "")[:200]}, output_data={"fs_json": state.get("fs_json", {})})

    return {"fs_json": state.get("fs_json", {}), "error": state.get("error")}


def generate_query_plan_node(state: AgentState) -> dict:
    """生成 Query Plan 节点"""
    from skills.generate_query_plan import generate_query_plan_skill
    state = generate_query_plan_skill.run(state)

    # Trace logging
    if HAS_TRACING:
        log_step("generate_query_plan", input_data={"fs_json": state.get("fs_json", {})}, output_data={"query_plan": state.get("query_plan", {})})

    return {"query_plan": state.get("query_plan", {}), "error": state.get("error")}


def generate_sql_node(state: AgentState) -> dict:
    """SQL 生成节点"""
    from skills.generate_sql import generate_sql_skill
    state = generate_sql_skill.run(state)

    # Trace logging
    if HAS_TRACING:
        tables = [t.get("table_name", "") for t in state.get("retrieved_tables", [])]
        log_generate_sql(tables, state.get("generated_sql", ""))

    return {"generated_sql": state.get("generated_sql", ""), "error": state.get("error")}


def validate_sql_node(state: AgentState) -> dict:
    """SQL 校验节点"""
    from skills.validate_sql import validate_sql_skill
    state = validate_sql_skill.run(state)

    # Trace logging
    is_valid = state.get("error") is None
    reason = state.get("error", "") if not is_valid else ""
    if HAS_TRACING:
        log_validate_sql(state.get("validated_sql", ""), is_valid, reason)

    return {"validated_sql": state.get("validated_sql", ""), "error": state.get("error")}


def route_datasource_node(state: AgentState) -> dict:
    """数据源路由节点"""
    from skills.route_datasource import route_datasource_skill
    state = route_datasource_skill.run(state)

    # Trace logging
    if HAS_TRACING:
        log_route_datasource(state.get("datasource", "postgresql"))

    return {"datasource": state.get("datasource", "postgresql")}


def execute_sql_node(state: AgentState) -> dict:
    """SQL 执行节点"""
    from skills.execute_sql import get_execute_sql_skill
    execute_sql_skill = get_execute_sql_skill()
    state = execute_sql_skill.run(state)

    # Trace logging
    if HAS_TRACING:
        sql = state.get("validated_sql", "")
        result = state.get("execution_result", {})
        row_count = result.get("row_count", 0) if isinstance(result, dict) else 0
        execution_time_ms = result.get("execution_time_ms", 0) if isinstance(result, dict) else 0
        error = state.get("error")
        log_execute_sql(sql, row_count, execution_time_ms, error)

    return {
        "execution_result": state.get("execution_result"),
        "error": state.get("error"),
        "retry_count": state.get("retry_count", 0)
    }


def repair_sql_node(state: AgentState) -> dict:
    """SQL 修复节点"""
    from skills.repair_sql import repair_sql_skill
    state = repair_sql_skill.run(state)

    # Trace logging
    if HAS_TRACING:
        original_sql = state.get("validated_sql", "")
        repaired_sql = state.get("generated_sql", "")
        error = state.get("error", "")
        attempt = state.get("retry_count", 1)
        log_repair_sql(original_sql, repaired_sql, error, attempt)

    return {"generated_sql": state.get("generated_sql", ""), "validated_sql": state.get("validated_sql", ""), "error": state.get("error")}


def format_result_node(state: AgentState) -> dict:
    """结果格式化节点"""
    from skills.format_result import format_result_skill
    return format_result_skill.run(state)


# ========== 条件函数 ==========

def should_retry(state: AgentState) -> str:
    """
    判断是否需要重试，最多重试 2 次（3 次执行机会）
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

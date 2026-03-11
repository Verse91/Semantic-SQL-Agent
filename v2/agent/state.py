"""
Agent State 定义
用于 LangGraph workflow 节点之间传递的状态
"""
from typing import TypedDict, List, Optional


class AgentState(TypedDict):
    """Agent 状态定义"""
    user_query: str                    # 用户查询
    conversation_history: List[dict]    # 对话历史
    schema_context: str               # Schema 上下文
    generated_sql: str                 # 生成的 SQL
    validated_sql: str                 # 校验后的 SQL
    datasource: str                    # 数据源 (hana/trino)
    execution_result: Optional[dict]    # 执行结果
    error: Optional[str]               # 错误信息
    retry_count: int                  # 重试次数

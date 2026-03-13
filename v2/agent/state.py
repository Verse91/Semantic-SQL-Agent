"""
Agent State 定义 (支持 FS)
用于 LangGraph workflow 节点之间传递的状态
"""
from typing import TypedDict, List, Optional, Dict, Any


class AgentState(TypedDict):
    """Agent 状态定义"""
    user_query: str                    # 用户查询
    fs_document: str                   # FS 文档内容
    fs_json: Dict[str, Any]           # FS 解析结果
    query_plan: Dict[str, Any]         # Query Plan
    schema_context: str               # Schema 上下文
    generated_sql: str                 # 生成的 SQL
    validated_sql: str                 # 校验后的 SQL
    datasource: str                    # 数据源 (hana/trino/postgresql)
    execution_result: Optional[Dict]   # 执行结果
    error: Optional[str]               # 错误信息
    retry_count: int                   # 重试次数
    conversation_history: List[Dict]   # 对话历史
    session_id: str                    # 会话 ID
    mode: str                          # 模式: "query" 或 "fs"

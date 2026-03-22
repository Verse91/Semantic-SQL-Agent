"""
Trace 日志工具 - 结构化日志
"""
import json
from typing import Any, Dict, Optional
from datetime import datetime
from .trace_models import TraceStep


class TraceLogger:
    """结构化日志工具"""
    
    def __init__(self):
        self._current_trace = None
    
    def set_trace(self, trace):
        """设置当前 trace"""
        self._current_trace = trace
    
    def clear_trace(self):
        """清除当前 trace"""
        self._current_trace = None
    
    def log_step(
        self,
        step_name: str,
        input_data: Dict[str, Any] = None,
        output_data: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> TraceStep:
        """
        记录步骤
        
        Args:
            step_name: 步骤名称
            input_data: 输入数据
            output_data: 输出数据
            metadata: 额外元数据
            
        Returns:
            TraceStep 对象
        """
        if input_data is None:
            input_data = {}
        if output_data is None:
            output_data = {}
        if metadata is None:
            metadata = {}
        
        step = TraceStep(
            step_name=step_name,
            input=self._sanitize(input_data),
            output=self._sanitize(output_data),
            metadata=metadata
        )
        
        if self._current_trace:
            self._current_trace.add_step(step)
        
        return step
    
    def _sanitize(self, data: Any) -> Any:
        """
        清理数据 - 移除敏感信息和过大数据
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # 跳过敏感字段
                if key.lower() in ('password', 'token', 'secret', 'key', 'api_key'):
                    result[key] = "***"
                elif isinstance(value, (str, int, float, bool, type(None))):
                    # 限制字符串长度
                    if isinstance(value, str) and len(value) > 10000:
                        result[key] = value[:10000] + "... [truncated]"
                    else:
                        result[key] = value
                elif isinstance(value, (list, dict)):
                    result[key] = self._sanitize(value)
                else:
                    result[key] = str(value)[:1000]
            return result
        elif isinstance(data, list):
            return [self._sanitize(item) for item in data[:100]]  # 限制列表长度
        else:
            return str(data)[:1000]
    
    # ============ 便捷方法 ============
    
    def log_schema_retriever(self, query: str, retrieved_tables: list, scores: list = None):
        """记录 schema 检索"""
        return self.log_step(
            step_name="schema_retriever",
            input_data={"query": query},
            output_data={
                "retrieved_tables": retrieved_tables,
                "similarity_scores": scores or []
            }
        )
    
    def log_generate_sql(self, tables: list, sql: str):
        """记录 SQL 生成"""
        return self.log_step(
            step_name="generate_sql",
            input_data={"input_tables": tables},
            output_data={"generated_sql": sql}
        )
    
    def log_validate_sql(self, sql: str, is_valid: bool, reason: str = ""):
        """记录 SQL 校验"""
        return self.log_step(
            step_name="validate_sql",
            input_data={"sql": sql},
            output_data={
                "is_valid": is_valid,
                "reason": reason
            }
        )
    
    def log_execute_sql(self, sql: str, row_count: int = 0, execution_time_ms: float = 0, error: str = None):
        """记录 SQL 执行"""
        return self.log_step(
            step_name="execute_sql",
            input_data={"sql": sql},
            output_data={
                "row_count": row_count,
                "execution_time_ms": execution_time_ms,
                "error": error
            }
        )
    
    def log_repair_sql(self, original_sql: str, repaired_sql: str, error_message: str, attempt: int = 1):
        """记录 SQL 修复"""
        return self.log_step(
            step_name="repair_sql",
            input_data={"original_sql": original_sql},
            output_data={
                "repaired_sql": repaired_sql,
                "error_message": error_message,
                "attempt": attempt
            }
        )
    
    def log_route_datasource(self, selected_datasource: str, available_datasources: list = None):
        """记录数据源路由"""
        return self.log_step(
            step_name="route_datasource",
            input_data={"available_datasources": available_datasources or []},
            output_data={"selected_datasource": selected_datasource}
        )


# 全局单例
_logger: Optional[TraceLogger] = None


def get_logger() -> TraceLogger:
    """获取 logger 实例"""
    global _logger
    if _logger is None:
        _logger = TraceLogger()
    return _logger

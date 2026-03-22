"""
Trace 管理器 - 核心控制器
"""
import uuid
from typing import Optional, List
from datetime import datetime
from .trace_models import QueryTrace
from .trace_storage import get_storage
from .trace_logger import get_logger


class TraceManager:
    """Trace 核心控制器"""
    
    def __init__(self):
        self._current_trace: Optional[QueryTrace] = None
    
    def start_trace(self, query: str, session_id: str = None) -> QueryTrace:
        """
        开始新的 Trace
        
        Args:
            query: 用户查询
            session_id: 会话 ID
            
        Returns:
            QueryTrace 对象
        """
        self._current_trace = QueryTrace(
            query=query,
            session_id=session_id
        )
        
        # 设置到 logger
        logger = get_logger()
        logger.set_trace(self._current_trace)
        
        return self._current_trace
    
    def get_current_trace(self) -> Optional[QueryTrace]:
        """获取当前 trace"""
        return self._current_trace
    
    def log_step(self, step_name: str, input_data: dict = None, output_data: dict = None, metadata: dict = None):
        """
        记录步骤
        
        Args:
            step_name: 步骤名称
            input_data: 输入数据
            output_data: 输出数据
            metadata: 额外元数据
        """
        logger = get_logger()
        return logger.log_step(step_name, input_data, output_data, metadata)
    
    def end_trace(self, status: str = "success") -> Optional[QueryTrace]:
        """
        结束 Trace
        
        Args:
            status: 状态 (success / failed)
            
        Returns:
            QueryTrace 对象
        """
        if self._current_trace:
            self._current_trace.finish(status)
            
            # 保存到存储
            storage = get_storage()
            storage.save_sync(self._current_trace)
            
            # 清除 logger
            logger = get_logger()
            logger.clear_trace()
            
            trace = self._current_trace
            self._current_trace = None
            return trace
        
        return None
    
    def finish(self, status: str = "success") -> Optional[QueryTrace]:
        """end_trace 的别名"""
        return self.end_trace(status)


# 全局单例
_manager: Optional[TraceManager] = None


def get_trace_manager() -> TraceManager:
    """获取 TraceManager 实例"""
    global _manager
    if _manager is None:
        _manager = TraceManager()
    return _manager


# ============ 便捷函数 ============

def start_trace(query: str, session_id: str = None) -> QueryTrace:
    """开始 trace"""
    return get_trace_manager().start_trace(query, session_id)


def log_step(step_name: str, input_data: dict = None, output_data: dict = None, metadata: dict = None):
    """记录步骤"""
    return get_trace_manager().log_step(step_name, input_data, output_data, metadata)


def end_trace(status: str = "success") -> Optional[QueryTrace]:
    """结束 trace"""
    return get_trace_manager().end_trace(status)


# ============ 便捷日志方法 ============

def log_schema_retriever(query: str, retrieved_tables: list, scores: list = None):
    """记录 schema 检索"""
    return get_logger().log_schema_retriever(query, retrieved_tables, scores)


def log_generate_sql(tables: list, sql: str):
    """记录 SQL 生成"""
    return get_logger().log_generate_sql(tables, sql)


def log_validate_sql(sql: str, is_valid: bool, reason: str = ""):
    """记录 SQL 校验"""
    return get_logger().log_validate_sql(sql, is_valid, reason)


def log_execute_sql(sql: str, row_count: int = 0, execution_time_ms: float = 0, error: str = None):
    """记录 SQL 执行"""
    return get_logger().log_execute_sql(sql, row_count, execution_time_ms, error)


def log_repair_sql(original_sql: str, repaired_sql: str, error_message: str, attempt: int = 1):
    """记录 SQL 修复"""
    return get_logger().log_repair_sql(original_sql, repaired_sql, error_message, attempt)


def log_route_datasource(selected_datasource: str, available_datasources: list = None):
    """记录数据源路由"""
    return get_logger().log_route_datasource(selected_datasource, available_datasources)

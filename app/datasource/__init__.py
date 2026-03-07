"""
数据源模块
支持多数据源查询路由: SAP HANA, Trino 等
"""

from .hana_executor import HanaExecutor, HanaError
from .router import QueryRouter, get_router

__all__ = [
    'HanaExecutor',
    'HanaError',
    'QueryRouter',
    'get_router',
]

"""
查询路由器
根据 SQL 涉及的表类型，将查询路由到不同的执行器
"""

import os
import re
import yaml
from typing import List, Dict, Any, Optional

from .hana_executor import HanaExecutor, HanaError


class QueryRouter:
    """
    SQL 查询路由器
    
    功能:
    - 识别 SQL 是否涉及 SAP 表
    - SAP 表查询路由到 HANA JDBC
    - 其他查询路由到默认执行器 (如 Trino)
    """
    
    def __init__(self, config_path: str = "config/database.yaml"):
        """
        初始化路由器
        
        Args:
            config_path: 配置文件路径
        """
        # 加载 SAP 表前缀配置
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path_full = os.path.join(project_root, config_path)
        
        with open(config_path_full, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 获取 SAP 表前缀列表
        self.sap_table_prefixes = config.get('sap_table_prefixes', [
            'MARA', 'VBAK', 'VBAP', 'BKPF', 'BSEG', 'EKKO', 'EKPO',
            'LFA1', 'KNA1', 'MAKT', 'T001', 'T001W', 'T003T'
        ])
        
        # 初始化 HANA 执行器
        self.hana_executor = HanaExecutor(config_path)
        
        # 默认执行器 (需要在外部注入)
        self.default_executor = None
    
    def set_default_executor(self, executor):
        """
        设置默认执行器 (如 Trino)
        
        Args:
            executor: 支持 run_query(sql) -> List[Dict] 的执行器
        """
        self.default_executor = executor
    
    def is_sap_query(self, sql: str) -> bool:
        """
        判断 SQL 是否涉及 SAP 表
        
        Args:
            sql: SQL 查询语句
            
        Returns:
            是否为 SAP 表查询
        """
        sql_upper = sql.upper()
        
        # 移除字符串字面量，避免误判
        sql_upper = re.sub(r"'[^']*'", "", sql_upper)
        sql_upper = re.sub(r'"[^"]*"', "", sql_upper)
        
        for table_prefix in self.sap_table_prefixes:
            # 匹配表名 (word boundary)
            pattern = r'\b' + table_prefix + r'\b'
            if re.search(pattern, sql_upper):
                return True
        
        return False
    
    def validate_sql(self, sql: str) -> None:
        """
        验证 SQL 安全性 - 只允许 SELECT
        
        Args:
            sql: SQL 查询语句
            
        Raises:
            Exception: 如果不是 SELECT 语句
        """
        sql_stripped = sql.strip().lower()
        
        # 检查是否以 SELECT 开头
        if not sql_stripped.startswith('select'):
            raise Exception("Security Error: Only SELECT queries are allowed")
        
        # 检查危险关键字
        dangerous_keywords = [
            'insert', 'update', 'delete', 'drop', 'create',
            'alter', 'truncate', 'exec', 'execute', 'call'
        ]
        
        for keyword in dangerous_keywords:
            if sql_stripped.startswith(keyword):
                raise Exception(f"Security Error: {keyword.upper()} is not allowed")
    
    def execute(self, sql: str) -> List[Dict[str, Any]]:
        """
        执行查询并路由到对应的执行器
        
        Args:
            sql: SELECT 查询语句
            
        Returns:
            查询结果列表
            
        Raises:
            Exception: 执行失败时
        """
        # 先验证 SQL 安全性
        self.validate_sql(sql)
        
        # 判断是否 SAP 查询
        if self.is_sap_query(sql):
            # 路由到 HANA
            return self.hana_executor.run_query(sql)
        else:
            # 路由到默认执行器
            if self.default_executor is None:
                raise Exception("No default executor configured")
            return self.default_executor.run_query(sql)


# 方便直接导入使用的单例
_default_router = None


def get_router() -> QueryRouter:
    """获取默认路由器实例"""
    global _default_router
    if _default_router is None:
        _default_router = QueryRouter()
    return _default_router

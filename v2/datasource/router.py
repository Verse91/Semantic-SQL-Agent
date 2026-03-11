"""
数据源路由器
"""
import re
from typing import Optional


class DatasourceRouter:
    """数据源路由器"""
    
    # SAP 表前缀
    SAP_TABLES = [
        "MARA", "VBAK", "VBAP", "BKPF", "BSEG", "EKKO", "EKPO",
        "LFA1", "KNA1", "MAKT", "T001", "T001W", "T003T",
        "MSEG", "MKOL", "KOMB", "VBRK", "VBRP"
    ]
    
    def __init__(self):
        pass
    
    def route(self, sql: str) -> str:
        """
        路由 SQL 到正确的执行器
        
        Args:
            sql: SQL 查询
            
        Returns:
            "hana" 或 "trino"
        """
        tables = self._extract_tables(sql)
        
        if self._is_sap_query(tables):
            return "hana"
        return "trino"
    
    def _extract_tables(self, sql: str) -> list:
        """提取表名"""
        pattern = r'(?:FROM|JOIN)\s+(\w+)'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        return [m.upper() for m in matches]
    
    def _is_sap_query(self, tables: list) -> bool:
        """判断是否 SAP 表查询"""
        for table in tables:
            for prefix in self.SAP_TABLES:
                if table.startswith(prefix):
                    return True
        return False


# 全局实例
_router = None


def get_router() -> DatasourceRouter:
    """获取路由器"""
    global _router
    if _router is None:
        _router = DatasourceRouter()
    return _router

"""
数据源路由 Skill
"""
import re
from typing import Dict, Any
from skills.base import BaseSkill


class RouteDatasourceSkill(BaseSkill):
    """数据源路由 Skill"""
    
    name = "route_datasource"
    description = "根据 SQL 表名自动路由到正确的数据源"
    
    # SAP 表前缀列表
    SAP_TABLE_PREFIXES = [
        "MARA", "VBAK", "VBAP", "BKPF", "BSEG", "EKKO", "EKPO",
        "LFA1", "KNA1", "MAKT", "T001", "T001W", "T003T",
        "MSEG", "MKOL", "KOMB", "VBRK", "VBRP"
    ]
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """路由数据源"""
        sql = state.get("validated_sql", "")
        
        # 提取 SQL 中的表名
        tables = self._extract_tables(sql)
        
        # 判断是否 SAP 表查询
        if self._is_sap_query(tables):
            state["datasource"] = "hana"
        else:
            state["datasource"] = "trino"
        
        return state
    
    def _extract_tables(self, sql: str) -> list:
        """从 SQL 中提取表名"""
        # 简单实现：匹配 FROM 和 JOIN 后的表名
        pattern = r'(?:FROM|JOIN)\s+(\w+)'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        return [m.upper() for m in matches]
    
    def _is_sap_query(self, tables: list) -> bool:
        """判断是否 SAP 表查询"""
        for table in tables:
            for prefix in self.SAP_TABLE_PREFIXES:
                if table.startswith(prefix):
                    return True
        return False


# 实例
route_datasource_skill = RouteDatasourceSkill()

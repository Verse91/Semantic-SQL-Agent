"""
Schema 加载器
从配置文件加载表结构
"""
import os
import yaml
from typing import Dict, List


class SchemaLoader:
    """Schema 加载器"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(project_root, 'config', 'schema.yaml')
        
        self.config_path = config_path
        self.config = {}
        self._load()
    
    def _load(self):
        """加载 Schema"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = self._default_config()
        
        # 将 schemas 结构扁平化为 tables
        self.schemas = self._flatten_schemas()
    
    def _flatten_schemas(self) -> Dict:
        """将多层 schema 结构扁平化"""
        tables = {}
        
        schemas = self.config.get("schemas", {})
        for schema_name, schema_info in schemas.items():
            schema_tables = schema_info.get("tables", {})
            for table_name, table_info in schema_tables.items():
                # 完整表名 = schema.table
                full_name = f"{schema_name}.{table_name}"
                tables[full_name] = table_info
        
        return {"tables": tables}
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "schemas": {
                "md": {
                    "tables": {
                        "mara": {
                            "description": "物料主数据表",
                            "columns": {"matnr": "物料号", "mtart": "物料类型"}
                        }
                    }
                }
            }
        }
    
    def get_table_schema(self, table_name: str) -> Dict:
        """获取表 Schema (支持短名和全名)"""
        # 尝试直接匹配
        if table_name in self.schemas.get("tables", {}):
            return self.schemas["tables"][table_name]
        
        # 尝试添加 schema 前缀
        for schema in ["md", "sd", "mm", "pp", "im"]:
            full_name = f"{schema}.{table_name}"
            if full_name in self.schemas.get("tables", {}):
                return self.schemas["tables"][full_name]
        
        return {}
    
    def get_all_tables(self) -> List[str]:
        """获取所有表"""
        return list(self.schemas.get("tables", {}).keys())
    
    def get_schema_text(self, query: str = None) -> str:
        """
        获取 Schema 文本
        
        Args:
            query: 用户查询 (用于关键词匹配)
        """
        all_tables = self.schemas.get("tables", {})
        
        if query:
            # 根据查询关键词筛选相关表
            query_lower = query.lower()
            relevant_tables = {}
            
            keywords = {
                "销售": ["sd", "订单", "客户", "发票", "发货"],
                "采购": ["mm", "供应商", "采购"],
                "生产": ["pp", "生产", "工序"],
                "库存": ["im", "库存", "物料"],
                "物料": ["mara", "makt", "marc"],
                "客户": ["kna1"],
                "供应商": ["lfa1"]
            }
            
            matched_schemas = set()
            for category, words in keywords.items():
                for word in words:
                    if word in query_lower:
                        matched_schemas.add(category)
            
            # 筛选相关 schema
            schema_map = {
                "销售": "sd", "采购": "mm", "生产": "pp", "库存": "im", "物料": "md", "客户": "md", "供应商": "md"
            }
            
            for matched in matched_schemas:
                schema = schema_map.get(matched, "")
                if schema:
                    for table in all_tables:
                        if table.startswith(schema + "."):
                            relevant_tables[table] = all_tables[table]
            
            if relevant_tables:
                all_tables = relevant_tables
        
        # 格式化输出
        lines = []
        for table, info in all_tables.items():
            lines.append(self._format_table(table, info))
        
        return "\n\n".join(lines)
    
    def _format_table(self, table: str, info: Dict) -> str:
        """格式化单个表"""
        desc = info.get("description", "")
        columns = info.get("columns", {})
        
        lines = [f"## {table}", f"**{desc}**"]
        for col, col_desc in columns.items():
            lines.append(f"- `{col}`: {col_desc}")
        
        return "\n".join(lines)
    
    def get_table_groups(self) -> Dict:
        """获取表分组"""
        return self.config.get("table_groups", {})
    
    def get_relationships(self) -> List[Dict]:
        """获取关联关系"""
        return self.config.get("relationships", [])

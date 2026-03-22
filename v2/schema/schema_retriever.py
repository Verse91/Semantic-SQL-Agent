"""
Schema 检索器
根据用户查询检索相关表结构
"""
import os
import sys
from typing import List, Optional

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from schema.schema_loader import SchemaLoader
from schema.schema_index import SchemaIndex

# 导入 trace 模块
try:
    from tracing import log_schema_retriever
    HAS_TRACING = True
except ImportError:
    HAS_TRACING = False


class SchemaRetriever:
    """Schema 检索器"""
    
    def __init__(self):
        self.loader = SchemaLoader()
        self.index = SchemaIndex()
        self._initialized = False
    
    def initialize(self):
        """初始化索引"""
        if self._initialized:
            return
        
        # 检查 FAISS 是否可用
        if not self.index.is_ready():
            # 如果没有向量索引，返回默认 Schema
            self._initialized = True
            return
        
        # 构建索引
        self._build_index()
        self._initialized = True
    
    def _build_index(self):
        """构建索引"""
        # TODO: 使用 embedding 模型生成向量
        # 目前暂时跳过
        pass
    
    def retrieve(self, query: str, top_k: int = 5) -> str:
        """
        检索相关 Schema
        
        Args:
            query: 用户查询
            top_k: 返回表数量
            
        Returns:
            Schema 上下文字符串
        """
        self.initialize()
        
        # 如果索引已构建，使用向量搜索
        if self.index.is_ready():
            # TODO: 生成查询向量
            # results = self.index.search(query_embedding, top_k)
            pass
        
        # 回退：返回所有表 Schema
        schema_text = self.loader.get_schema_text()
        
        # 提取表名列表
        tables = self._extract_tables(schema_text)
        
        # Trace logging (scores is empty since vector similarity not implemented)
        if HAS_TRACING:
            log_schema_retriever(query, tables, scores=[])
        
        return schema_text
    
    def retrieve_with_tables(self, query: str, top_k: int = 5) -> tuple:
        """
        检索相关 Schema 并返回表名列表
        
        Args:
            query: 用户查询
            top_k: 返回表数量
            
        Returns:
            (schema_text, tables) 元组
        """
        schema_text = self.retrieve(query, top_k)
        tables = self._extract_tables(schema_text)
        return schema_text, tables
    
    def _extract_tables(self, schema_text: str) -> List[str]:
        """从 schema 文本中提取表名"""
        import re
        # 匹配 ## schema.table 格式 (如 md.kna1, sd.vbak)
        tables = re.findall(r'## (\w+\.\w+)', schema_text)
        return tables[:10]  # 限制数量
    
    def get_table_schema(self, table_name: str) -> dict:
        """获取单个表的 Schema"""
        return self.loader.get_table_schema(table_name)


# 全局实例
_retriever = None


def get_schema_retriever() -> SchemaRetriever:
    """获取 Schema 检索器"""
    global _retriever
    if _retriever is None:
        _retriever = SchemaRetriever()
    return _retriever


def retrieve_schema(query: str) -> str:
    """便捷函数：检索 Schema"""
    retriever = get_schema_retriever()
    return retriever.retrieve(query)

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
        return self.loader.get_schema_text()
    
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

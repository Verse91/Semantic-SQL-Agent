"""
Schema 索引
使用 FAISS 构建向量索引
"""
import os
import numpy as np
from typing import List, Optional

# 尝试导入 faiss
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class SchemaIndex:
    """Schema 向量索引"""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = None
        self.tables = []
        self.embeddings = {}
        
        if FAISS_AVAILABLE:
            self.index = faiss.IndexFlatL2(dimension)
    
    def add_table(self, table_name: str, description: str, embedding: np.ndarray):
        """
        添加表到索引
        
        Args:
            table_name: 表名
            description: 表描述
            embedding: 向量
        """
        if self.index is None:
            return
        
        # 归一化
        embedding = embedding / np.linalg.norm(embedding)
        
        self.index.add(embedding.reshape(1, -1))
        self.tables.append({
            "name": table_name,
            "description": description
        })
        self.embeddings[table_name] = embedding
    
    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> List[dict]:
        """
        搜索相关表
        
        Args:
            query_embedding: 查询向量
            top_k: 返回数量
            
        Returns:
            相关表列表
        """
        if self.index is None or len(self.tables) == 0:
            return []
        
        # 归一化
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # 搜索
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1), 
            min(top_k, len(self.tables))
        )
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0:
                results.append({
                    "table": self.tables[idx]["name"],
                    "description": self.tables[idx]["description"],
                    "distance": float(distances[0][i])
                })
        
        return results
    
    def is_ready(self) -> bool:
        """检查索引是否就绪"""
        return self.index is not None and self.index.ntotal > 0


# 全局实例
_index = None


def get_schema_index() -> SchemaIndex:
    """获取 Schema 索引"""
    global _index
    if _index is None:
        _index = SchemaIndex()
    return _index

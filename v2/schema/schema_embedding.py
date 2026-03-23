"""
Schema Embedding 模块
使用 sentence-transformers 生成向量并构建 FAISS 索引
"""
import os
import pickle
import numpy as np
from typing import List, Dict, Optional

# 尝试导入 sentence_transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# 尝试导入 faiss
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class SchemaEmbedding:
    """Schema 向量嵌入"""
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # MiniLM-L12 default dimension
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception as e:
                print(f"Failed to load embedding model: {e}")
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.model is not None
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """
        生成文本向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量数组 (N, dimension)
        """
        if self.model is None:
            raise RuntimeError("Embedding model not available")
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings
    
    def encode_single(self, text: str) -> np.ndarray:
        """生成单个文本向量"""
        return self.encode([text])[0]


class SchemaVectorStore:
    """Schema 向量存储"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(project_root, 'schema')
        
        self.cache_dir = cache_dir
        self.embedding = SchemaEmbedding()
        self.index = None
        self.tables = []  # 表信息列表
        self.embeddings = None
        
        # 确保缓存目录存在
        os.makedirs(cache_dir, exist_ok=True)
        
        self._load_index()
    
    def _get_cache_path(self) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, 'schema_index.pkl')
    
    def _load_index(self):
        """加载索引"""
        cache_path = self._get_cache_path()
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                    self.index = data.get('index')
                    self.tables = data.get('tables', [])
                    self.embeddings = data.get('embeddings')
                print(f"Loaded index with {len(self.tables)} tables")
            except Exception as e:
                print(f"Failed to load index: {e}")
    
    def build_index(self, schema_data: Dict[str, Dict]):
        """
        构建向量索引
        
        Args:
            schema_data: {table_name: {description: str, columns: dict}}
        """
        if not self.embedding.is_available():
            print("Embedding model not available, skipping index build")
            return
        
        # 准备表描述文本
        table_texts = []
        table_names = []
        
        for table_name, info in schema_data.items():
            # 构建描述文本：表名 + 描述 + 列信息
            desc = info.get('description', '')
            columns = info.get('columns', {})
            
            # 列名和描述
            col_text = ', '.join([f"{col}: {col_desc}" for col, col_desc in columns.items()])
            
            # 完整描述
            full_text = f"{table_name}: {desc}. Columns: {col_text}"
            
            table_texts.append(full_text)
            table_names.append(table_name)
        
        # 生成向量
        print(f"Generating embeddings for {len(table_texts)} tables...")
        embeddings = self.embedding.encode(table_texts)
        
        # 构建 FAISS 索引 (使用内积，因为向量已经归一化)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        
        # 归一化向量
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / norms
        
        self.index.add(normalized)
        self.tables = table_names
        self.embeddings = embeddings
        
        # 保存索引
        self._save_index()
        
        print(f"Built index with {self.index.ntotal} tables")
    
    def _save_index(self):
        """保存索引"""
        cache_path = self._get_cache_path()
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump({
                    'index': self.index,
                    'tables': self.tables,
                    'embeddings': self.embeddings
                }, f)
            print(f"Saved index to {cache_path}")
        except Exception as e:
            print(f"Failed to save index: {e}")
    
    def is_ready(self) -> bool:
        """检查索引是否就绪"""
        return self.index is not None and self.index.ntotal > 0
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        搜索相关表
        
        Args:
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            [{table: str, score: float, description: str}]
        """
        if not self.is_ready():
            return []
        
        # 生成查询向量
        query_embedding = self.embedding.encode_single(query)
        
        # 归一化
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # 搜索
        scores, indices = self.index.search(
            query_embedding.reshape(1, -1), 
            min(top_k, len(self.tables))
        )
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0:
                # 转换为相似度 (1 - 距离), 因为使用内积
                similarity = float(scores[0][i])
                results.append({
                    "table": self.tables[idx],
                    "score": similarity,
                })
        
        return results


# 全局实例
_embedding_store = None


def get_schema_vector_store() -> SchemaVectorStore:
    """获取向量存储实例"""
    global _embedding_store
    if _embedding_store is None:
        _embedding_store = SchemaVectorStore()
    return _embedding_store

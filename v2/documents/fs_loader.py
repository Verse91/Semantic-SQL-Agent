"""
FS Loader - 报表文件加载器
支持读取 txt, md, pdf, docx 格式
"""
import os
from typing import Optional


class FSLoader:
    """FS 报表文件加载器"""
    
    SUPPORTED_EXTENSIONS = ['.txt', '.md', '.pdf', '.docx']
    
    def load(self, file_path: str) -> str:
        """
        加载 FS 文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档内容文本
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")
        
        if ext in ['.txt', '.md']:
            return self._load_text(file_path)
        elif ext == '.pdf':
            return self._load_pdf(file_path)
        elif ext == '.docx':
            return self._load_docx(file_path)
    
    def _load_text(self, file_path: str) -> str:
        """加载文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_pdf(self, file_path: str) -> str:
        """加载 PDF 文件"""
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            raise ImportError("pypdf is required. Install with: pip install pypdf")
    
    def _load_docx(self, file_path: str) -> str:
        """加载 DOCX 文件"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            raise ImportError("python-docx is required. Install with: pip install python-docx")


# 全局实例
_loader = None


def get_fs_loader() -> FSLoader:
    """获取 FS Loader 实例"""
    global _loader
    if _loader is None:
        _loader = FSLoader()
    return _loader


def load_fs(file_path: str) -> str:
    """便捷函数：加载 FS 文档"""
    return get_fs_loader().load(file_path)

"""
对话记忆
"""
import json
import os
from typing import List, Dict, Optional
from datetime import datetime


class ConversationMemory:
    """对话记忆"""
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            home = os.path.expanduser("~")
            storage_path = os.path.join(home, ".semantic_sql_agent", "memory")
        
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def _get_file_path(self, session_id: str) -> str:
        """获取会话文件路径"""
        return os.path.join(self.storage_path, f"{session_id}.json")
    
    def get(self, session_id: str) -> List[Dict]:
        """
        获取会话历史
        
        Args:
            session_id: 会话 ID
            
        Returns:
            对话历史列表
        """
        file_path = self._get_file_path(session_id)
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("history", [])
        
        return []
    
    def add(self, session_id: str, role: str, content: str):
        """
        添加对话
        
        Args:
            session_id: 会话 ID
            role: 角色 (user/assistant)
            content: 内容
        """
        file_path = self._get_file_path(session_id)
        
        # 读取现有数据
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"session_id": session_id, "history": []}
        
        # 添加新对话
        data["history"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # 保存
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def clear(self, session_id: str):
        """清除会话"""
        file_path = self._get_file_path(session_id)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    def get_recent(self, session_id: str, count: int = 4) -> List[Dict]:
        """获取最近 N 条对话"""
        history = self.get(session_id)
        return history[-count:] if len(history) > count else history


# 全局实例
_memory = None


def get_conversation_memory() -> ConversationMemory:
    """获取对话记忆"""
    global _memory
    if _memory is None:
        _memory = ConversationMemory()
    return _memory

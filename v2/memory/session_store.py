"""
会话存储
"""
import json
import os
import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta


class SessionStore:
    """会话存储"""
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            home = os.path.expanduser("~")
            storage_path = os.path.join(home, ".semantic_sql_agent", "sessions")
        
        self.storage_path = storage_path
        self.sessions_file = os.path.join(self.storage_path, "sessions.json")
        os.makedirs(storage_path, exist_ok=True)
        
        self._load_sessions()
    
    def _load_sessions(self):
        """加载会话"""
        if os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                self.sessions = json.load(f)
        else:
            self.sessions = {}
    
    def _save_sessions(self):
        """保存会话"""
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(self.sessions, f, ensure_ascii=False, indent=2)
    
    def create(self, session_id: str = None) -> str:
        """
        创建会话
        
        Args:
            session_id: 会话 ID (可选)
            
        Returns:
            session_id
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "metadata": {}
        }
        
        self._save_sessions()
        return session_id
    
    def get(self, session_id: str) -> Optional[Dict]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def update(self, session_id: str, metadata: Dict):
        """更新会话"""
        if session_id in self.sessions:
            self.sessions[session_id]["last_active"] = datetime.now().isoformat()
            self.sessions[session_id]["metadata"].update(metadata)
            self._save_sessions()
    
    def delete(self, session_id: str):
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
    
    def cleanup(self, hours: int = 24):
        """清理过期会话"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        to_delete = []
        for sid, session in self.sessions.items():
            last_active = datetime.fromisoformat(session["last_active"])
            if last_active < cutoff:
                to_delete.append(sid)
        
        for sid in to_delete:
            del self.sessions[sid]
        
        if to_delete:
            self._save_sessions()


# 全局实例
_store = None


def get_session_store() -> SessionStore:
    """获取会话存储"""
    global _store
    if _store is None:
        _store = SessionStore()
    return _store

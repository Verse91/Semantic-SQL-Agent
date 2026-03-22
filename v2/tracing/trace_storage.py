"""
Trace 存储模块 - JSON 文件存储
"""
import os
import json
import asyncio
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from .trace_models import QueryTrace


class TraceStorage:
    """JSON 文件存储"""
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "traces"
            )
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._write_queue: asyncio.Queue = asyncio.Queue()
        self._write_task: Optional[asyncio.Task] = None
    
    def _get_date_dir(self) -> Path:
        """获取当日目录"""
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = self.base_dir / today
        date_dir.mkdir(parents=True, exist_ok=True)
        return date_dir
    
    def _get_trace_path(self, trace_id: str) -> Path:
        """获取 trace 文件路径"""
        date_dir = self._get_date_dir()
        return date_dir / f"trace_{trace_id}.json"
    
    async def save(self, trace: QueryTrace):
        """异步保存 trace"""
        trace_path = self._get_trace_path(trace.trace_id)
        with open(trace_path, 'w', encoding='utf-8') as f:
            json.dump(trace.to_dict(), f, ensure_ascii=False, indent=2)
    
    def save_sync(self, trace: QueryTrace):
        """同步保存 trace"""
        trace_path = self._get_trace_path(trace.trace_id)
        with open(trace_path, 'w', encoding='utf-8') as f:
            json.dump(trace.to_dict(), f, ensure_ascii=False, indent=2)
    
    def get(self, trace_id: str, date: str = None) -> Optional[dict]:
        """读取单条 trace"""
        if date:
            trace_path = self.base_dir / date / f"trace_{trace_id}.json"
        else:
            # 搜索所有日期目录
            for date_dir in self.base_dir.iterdir():
                if date_dir.is_dir():
                    trace_path = date_dir / f"trace_{trace_id}.json"
                    if trace_path.exists():
                        break
            else:
                return None
        
        if trace_path.exists():
            with open(trace_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def list_traces(self, date: str = None, limit: int = 50) -> List[dict]:
        """列出 traces"""
        if date:
            date_dir = self.base_dir / date
        else:
            # 获取最新的日期目录
            date_dirs = sorted([d for d in self.base_dir.iterdir() if d.is_dir()], reverse=True)
            date_dir = date_dirs[0] if date_dirs else None
        
        if not date_dir:
            return []
        
        traces = []
        for trace_file in sorted(date_dir.glob("trace_*.json"), reverse=True)[:limit]:
            with open(trace_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 只返回概要信息
                traces.append({
                    "trace_id": data.get("trace_id"),
                    "query": data.get("query"),
                    "status": data.get("status"),
                    "start_time": data.get("start_time"),
                    "end_time": data.get("end_time"),
                    "step_count": len(data.get("steps", []))
                })
        
        return traces


# 全局单例
_storage: Optional[TraceStorage] = None


def get_storage() -> TraceStorage:
    """获取存储实例"""
    global _storage
    if _storage is None:
        _storage = TraceStorage()
    return _storage

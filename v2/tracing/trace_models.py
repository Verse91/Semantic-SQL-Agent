"""
Trace 数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid


class TraceStep(BaseModel):
    """单步执行记录"""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueryTrace(BaseModel):
    """完整 Query 执行轨迹"""
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    query: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    steps: List[TraceStep] = Field(default_factory=list)
    status: str = "running"  # running / success / failed
    
    def add_step(self, step: TraceStep):
        """添加步骤"""
        self.steps.append(step)
    
    def finish(self, status: str = "success"):
        """结束 Trace"""
        self.end_time = datetime.now()
        self.status = status
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "query": self.query,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "steps": [
                {
                    "step_id": s.step_id,
                    "step_name": s.step_name,
                    "timestamp": s.timestamp.isoformat(),
                    "input": s.input,
                    "output": s.output,
                    "metadata": s.metadata
                }
                for s in self.steps
            ]
        }

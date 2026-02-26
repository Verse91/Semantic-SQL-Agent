from pydantic import BaseModel
from typing import Optional, List, Any


class GenerateSQLRequest(BaseModel):
    question: str


class GenerateSQLResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class ExecuteSQLRequest(BaseModel):
    sql: str


class ExecuteSQLResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None

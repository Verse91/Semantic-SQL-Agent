from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class ReportMode(str, Enum):
    NATURAL_LANGUAGE = "natural_language"
    REPORT_DSL = "report_dsl"


class Metric(BaseModel):
    name: str
    expression: str


class ReportSpec(BaseModel):
    name: str
    tables: List[str]
    joins: List[str]
    metrics: List[Metric]
    dimensions: List[str]
    filters: List[str]


class UploadReportRequest(BaseModel):
    pass


class UploadReportResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class GenerateSQLFromSpecRequest(BaseModel):
    report_spec: dict


class QueryRequest(BaseModel):
    question: str
    mode: ReportMode = ReportMode.NATURAL_LANGUAGE

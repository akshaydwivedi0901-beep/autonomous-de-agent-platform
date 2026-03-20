"""API models (pydantic)"""

from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str


class QueryRequest(BaseModel):
    question: str
    environment: Optional[str] = "dev"


class QueryResponse(BaseModel):
    execution_id: str
    answer: Optional[str] = None
    sql: Optional[str] = None
    rows: Optional[int] = None
    status: str

class QueryRequest(BaseModel):
    question: str
    session_id: str
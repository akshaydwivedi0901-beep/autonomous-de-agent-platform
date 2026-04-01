from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid


class AgentState(BaseModel):

    # =============================
    # INPUT
    # =============================
    question: str
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    environment: Optional[str] = "dev"

    # =============================
    # CONVERSATION (multi-turn)
    # =============================
    conversation_history: List[Any] = Field(default_factory=list)

    # =============================
    # BA OUTPUT
    # =============================
    business_analysis: Optional[Any] = None
    intent: Optional[str] = None

    # =============================
    # ROUTING
    # =============================
    route: Optional[str] = None  # "SQL" | "RAG" | "HYBRID"

    # =============================
    # RAG
    # =============================
    rag_context: Optional[str] = None

    # =============================
    # SQL LAYER
    # =============================
    generated_sql: Optional[str] = None
    validated_sql: Optional[str] = None

    # =============================
    # VALIDATION
    # =============================
    validation_status: Optional[str] = None

    # =============================
    # GOVERNANCE
    # =============================
    governance_status: Optional[str] = None
    risk_score: Optional[int] = 0

    # =============================
    # EXECUTION
    # =============================
    execution_result: Optional[Dict[str, Any]] = None
    rows: Optional[List[Any]] = None
    row_count: Optional[int] = None
    execution_time: Optional[float] = None
    query_id: Optional[str] = None

    # =============================
    # FINAL OUTPUT
    # =============================
    final_answer: Optional[str] = None
    explanation: Optional[str] = None

    # =============================
    # ERROR HANDLING
    # =============================
    error: Optional[str] = None

    # =============================
    # STATUS
    # =============================
    status: Optional[str] = None

    # =============================
    # RETRY CONTROL
    # =============================
    retry_count: int = 0
    max_retries: int = 2

    class Config:
        arbitrary_types_allowed = True
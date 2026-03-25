from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class AgentState(BaseModel):
    # =============================
    # INPUT
    # =============================
    question: str

    # =============================
    # CONVERSATION
    # =============================
    conversation_history: List[Any] = Field(default_factory=list)

    # =============================
    # BA OUTPUT
    # =============================
    business_analysis: Optional[Any] = None

    # =============================
    # ROUTING
    # =============================
    route: Optional[str] = None

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
    # EXECUTION
    # =============================
    execution_result: Optional[Dict[str, Any]] = None
    rows: Optional[List[Any]] = None
    row_count: Optional[int] = None
    execution_time: Optional[float] = None

    # =============================
    # FINAL OUTPUT
    # =============================
    final_answer: Optional[str] = None

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
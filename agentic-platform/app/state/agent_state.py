from pydantic import BaseModel
from typing import Optional, List


class AgentState(BaseModel):

    question: str

    execution_id: Optional[str] = None

    session_id: Optional[str] = None

    conversation_history: List = []

    route: Optional[str] = None

    generated_sql: Optional[str] = None
    validated_sql: Optional[str] = None

    validation_status: Optional[str] = None

    explanation: Optional[str] = None

    status: Optional[str] = None

    retry_count: int = 0

    row_count: Optional[int] = None

    rag_context: Optional[str] = None
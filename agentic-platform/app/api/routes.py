import logging

from fastapi import APIRouter, HTTPException

from app.state.agent_state import AgentState
from app.orchestrator.graph import build_graph
from app.api.models import QueryRequest, QueryResponse
from app.memory.redis_memory import RedisMemory

logger = logging.getLogger(__name__)

router = APIRouter()

# Build graph once at startup (thread-safe, reused across requests)
graph = build_graph()
memory = RedisMemory()


@router.post("/execute", response_model=QueryResponse)
async def execute(request: QueryRequest):

    session_id = request.session_id

    # =============================
    # LOAD CONVERSATION HISTORY
    # =============================
    history = memory.get_recent_context(session_id, turns=6)

    # =============================
    # BUILD STATE
    # =============================
    state = AgentState(
        question=request.question,
        session_id=session_id,
        environment=request.environment or "dev",
        conversation_history=history,
    )

    # =============================
    # RUN GRAPH (sync invoke — LangGraph compiled graphs are sync)
    # =============================
    try:
        result = graph.invoke(state)

        if isinstance(result, dict):
            result = AgentState(**result)

    except Exception as e:
        logger.exception("Graph execution failed")
        raise HTTPException(status_code=500, detail=str(e))

    # =============================
    # PERSIST TURN TO MEMORY
    # =============================
    try:
        memory.append_message(session_id, "user", request.question)
        memory.append_message(
            session_id,
            "assistant",
            result.final_answer or result.explanation or "",
        )
    except Exception as e:
        logger.warning(f"Memory save failed (non-fatal): {e}")

    # =============================
    # RESPONSE
    # =============================
    return QueryResponse(
        execution_id=result.execution_id or "N/A",
        answer=result.final_answer or result.explanation or "No response generated",
        sql=result.validated_sql,
        rows=result.row_count or 0,
        status=result.status or "UNKNOWN",
    )
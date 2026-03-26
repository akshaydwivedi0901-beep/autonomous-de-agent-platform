import logging

from fastapi import APIRouter, HTTPException

from app.api.chat_api import router as chat_router
from app.api.health_api import router as health_router
from app.api.metrics_api import router as metrics_router

from app.state.agent_state import AgentState
from app.orchestrator.graph import build_graph
from app.api.models import QueryRequest, QueryResponse

from app.memory.redis_memory import RedisMemory

logger = logging.getLogger(__name__)

router = APIRouter()

router.include_router(chat_router)
router.include_router(health_router)
router.include_router(metrics_router)

graph = build_graph()

# ✅ Keep Redis optional
memory = RedisMemory()


@router.post("/execute")
async def execute(request: QueryRequest):

    session_id = request.session_id

    # =============================
    # LOAD MEMORY (SAFE MODE)
    # =============================
    try:
        history = memory.get_history(session_id)
    except Exception as e:
        logger.warning(f"Redis not available, skipping memory: {e}")
        history = []

    state = AgentState(
        question=request.question,
        session_id=session_id,
        conversation_history=history
    )

    # =============================
    # GRAPH EXECUTION (SAFE)
    # =============================
    try:
        result = await graph.ainvoke(state)

    except Exception as e:
        logger.exception("Graph execution failed")

        return QueryResponse(
            execution_id="FAILED",
            answer="Sorry, something went wrong while processing your request.",
            sql=None,
            rows=0,
            status="FAILED"
        )

    # =============================
    # SAVE MEMORY (SAFE MODE)
    # =============================
    try:
        memory.append_message(
            session_id,
            "user",
            request.question
        )

        memory.append_message(
            session_id,
            "assistant",
            result.explanation
        )

    except Exception as e:
        logger.warning(f"Redis not available, skipping save: {e}")

    # =============================
    # RESPONSE (SAFE ACCESS)
    # =============================
    return QueryResponse(
        execution_id=getattr(result, "execution_id", "N/A"),
        answer=getattr(result, "explanation", "No response generated"),
        sql=getattr(result, "validated_sql", None),
        rows=getattr(result, "row_count", 0),
        status=getattr(result, "status", "UNKNOWN")
    )
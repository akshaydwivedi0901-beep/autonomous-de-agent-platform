import uuid
import logging

from fastapi import APIRouter
from app.api.router import router as execute_router
from app.api.chat_api import router as chat_router
from app.api.health_api import router as health_router
from app.api.metrics_api import router as metrics_router

from app.state.agent_state import AgentState
from app.orchestrator.graph import build_graph
from app.api.models import QueryRequest, QueryResponse

from app.memory.redis_memory import RedisMemory

logger = logging.getLogger(__name__)

router = APIRouter()
router.include_router(execute_router)
router.include_router(chat_router)
router.include_router(health_router)
router.include_router(metrics_router)
graph = build_graph()

memory = RedisMemory()


@router.post("/execute")
async def execute(request: QueryRequest):

    session_id = request.session_id

    history = memory.get_history(session_id)

    state = AgentState(
        question=request.question,
        session_id=session_id,
        conversation_history=history
    )

    result = graph.invoke(state)

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

    return QueryResponse(
        execution_id=result.execution_id,
        answer=result.explanation,
        sql=result.validated_sql,
        rows=result.row_count,
        status=result.status
    )
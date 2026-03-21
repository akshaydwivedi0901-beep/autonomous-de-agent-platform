import logging
from fastapi import APIRouter, HTTPException

from app.state.agent_state import AgentState
from app.api.models import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/execute", response_model=QueryResponse)
async def execute(request: QueryRequest):
    try:
        # ✅ Lazy import to avoid circular dependency
        from app.orchestrator.graph import build_graph

        graph = build_graph()

        state = AgentState(
            question=request.question,
            environment=request.environment
        )

        result = graph.invoke(state)

        return QueryResponse(
            execution_id=result.execution_id,
            answer=result.explanation,
            sql=result.validated_sql,
            rows=result.row_count,
            status=result.status
        )

    except Exception as e:
        logger.exception("Agent execution failed")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
import logging
from fastapi import APIRouter, HTTPException

from app.state.agent_state import AgentState
from app.orchestrator.graph import build_graph
from app.api.models import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

router = APIRouter()

graph = build_graph()


@router.post("/execute", response_model=QueryResponse)
async def execute(request: QueryRequest):

    try:

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
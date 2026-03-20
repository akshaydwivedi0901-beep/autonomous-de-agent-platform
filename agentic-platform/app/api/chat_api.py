from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import asyncio

from app.state.agent_state import AgentState
from app.orchestrator.graph import build_graph

router = APIRouter()

graph = build_graph()


@router.post("/chat/stream")
async def chat_stream(query: dict):

    async def event_generator():

        state = AgentState(question=query["question"])

        result = graph.invoke(state)

        text = result.explanation if result.explanation else str(result)

        for token in text.split():
            yield {
                "event": "message",
                "data": token + " "
            }
            await asyncio.sleep(0.02)

    return EventSourceResponse(event_generator())
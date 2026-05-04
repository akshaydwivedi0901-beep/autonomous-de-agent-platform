import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.state.agent_state import AgentState
from app.orchestrator.graph import build_graph

logger = logging.getLogger(__name__)

router = APIRouter()

graph = build_graph()


# =========================================
# STREAM HELPER
# =========================================
def format_sse(event: str, data: str):
    return f"event: {event}\ndata: {data}\n\n"


# =========================================
# STREAM API
# =========================================
@router.post("/chat/stream")
async def chat_stream(request: Request):

    body = await request.json()
    question = body.get("question")

    async def event_generator():
        try:
            # Step 1: Initial message
            yield format_sse("message", "Processing your request...")

            # Step 2: Create state
            state = AgentState(
                question=question,
                conversation_history=[]
            )

            # Step 3: Run graph
            result = graph.invoke(state)

            #  IMPORTANT: handle dict vs AgentState
            if isinstance(result, dict):
                logger.warning(" Graph returned dict → converting to AgentState")
                state = AgentState(**result)
            else:
                state = result

            logger.info(f"FINAL STATUS: {state.status}")

            # =========================================
            # FINAL OUTPUT LOGIC (CRITICAL FIX)
            # =========================================

            # 1️ If final_answer exists → use it
            if getattr(state, "final_answer", None):
                yield format_sse("message", state.final_answer)

            # 2️ If execution_result exists → fallback
            elif getattr(state, "execution_result", None):
                result = state.execution_result
                value = result.get("value")
                exec_time = result.get("execution_time")

                yield format_sse(
                    "message",
                    f"Result: {value} (Execution time: {exec_time}s)"
                )

            # 3️ If business_analysis exists
            elif getattr(state, "business_analysis", None):
                yield format_sse("message", state.business_analysis)

            # 4️ If SQL exists
            elif getattr(state, "sql_query", None):
                yield format_sse("message", f"SQL Generated:\n{state.sql_query}")

            # 5️ Error fallback
            else:
                yield format_sse(
                    "message",
                    " I couldn't generate a reliable answer. Please rephrase your question."
                )

        except Exception as e:
            logger.exception(" STREAM FAILED")

            yield format_sse(
                "error",
                f"Internal error: {str(e)}"
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# =========================================
# NON-STREAM API (DEBUG)
# =========================================
@router.post("/chat")
async def chat(request: Request):

    try:
        body = await request.json()
        question = body.get("question")

        state = AgentState(
            question=question,
            conversation_history=[]
        )

        result = graph.invoke(state)

        if isinstance(result, dict):
            state = AgentState(**result)
        else:
            state = result

        return {
            "status": state.status,
            "answer": getattr(state, "final_answer", None),
            "execution_result": getattr(state, "execution_result", None),
            "sql": getattr(state, "sql_query", None)
        }

    except Exception as e:
        logger.exception(" CHAT FAILED")

        return {
            "error": str(e)
        }
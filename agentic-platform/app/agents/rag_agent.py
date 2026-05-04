import logging

from app.state.agent_state import AgentState
from app.rag.retriever import retrieve_context

logger = logging.getLogger(__name__)


def rag_agent(state: AgentState):

    try:
        logger.info(" RAG AGENT START")

        question = state.question

        # =============================
        # RETRIEVE CONTEXT
        # =============================
        try:
            context = retrieve_context(question)
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            context = ""

        # Ensure string
        if isinstance(context, dict):
            state.rag_context = context.get("context", "")
        else:
            state.rag_context = str(context)

        # =============================
        # SIMPLE RESPONSE (can improve later)
        # =============================
        state.explanation = f"Based on available knowledge: {state.rag_context}"
        state.status = "RAG_COMPLETE"

        logger.info({
            "execution_id": state.execution_id,
            "agent": "rag",
            "status": state.status
        })

        #  FIXED MEMORY
        state.conversation_history.append({
            "role": "system",
            "message": "RAG_AGENT"
        })

        return state

    except Exception as e:
        logger.exception(" RAG AGENT FAILED")

        state.status = "RAG_FAILED"
        state.error = str(e)

        return state
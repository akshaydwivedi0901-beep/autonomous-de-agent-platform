import logging
from app.state.agent_state import AgentState
from app.rag.retriever import retrieve_context

logger = logging.getLogger(__name__)


def rag_agent(state: AgentState):

    context = retrieve_context(state.question)

    state.rag_context = context
    state.status = "RAG_COMPLETE"

    state.history.append("RAG_AGENT")

    logger.info({
        "execution_id": state.execution_id,
        "agent": "rag",
        "context_length": len(context)
    })

    return state

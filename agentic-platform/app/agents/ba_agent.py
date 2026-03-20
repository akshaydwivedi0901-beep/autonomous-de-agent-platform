import logging
import uuid

from app.state.agent_state import AgentState
from app.orchestrator.llm_router import LLMRouter
from app.rag.retriever import retrieve_context

logger = logging.getLogger(__name__)


def ba_agent(state: AgentState):

    if not state.execution_id:
        state.execution_id = str(uuid.uuid4())

    llm = LLMRouter.get_llm("planner", state.question)

    question = state.question

    # RAG context
    try:
        rag_context = retrieve_context(question)
    except Exception:
        rag_context = ""

    state.rag_context = rag_context

    history = ""

    if state.conversation_history:
        history = "\n".join(
            [f"{m['role']}: {m['message']}" for m in state.conversation_history]
        )

    prompt = f"""
You are a Business Analyst.

Conversation history:
{history}

Business knowledge:
{rag_context}

Question:
{question}

Explain:
1. Business metric
2. Filters
3. Tables required
4. Columns required
"""

    response = llm.invoke(prompt)

    state.business_analysis = response.content.strip()
    state.status = "BA_COMPLETE"

    logger.info({
        "execution_id": state.execution_id,
        "agent": "ba",
        "status": state.status
    })

    state.history.append("BA_AGENT")

    return state
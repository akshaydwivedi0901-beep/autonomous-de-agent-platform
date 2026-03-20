import logging

from app.state.agent_state import AgentState
from app.orchestrator.llm_router import LLMRouter

logger = logging.getLogger(__name__)


def explain_agent(state: AgentState):

    llm = LLMRouter.get_llm("explain")

    prompt = f"""
Explain the SQL result to a business user.

Question:
{state.question}

SQL:
{state.validated_sql}

Provide a clear explanation.
"""

    response = llm.invoke(prompt)

    state.explanation = response.content.strip()
    state.status = "EXPLAIN_COMPLETE"

    logger.info({
        "execution_id": state.execution_id,
        "agent": "explain"
    })

    state.history.append("EXPLAIN_AGENT")

    return state
import logging

from app.state.agent_state import AgentState
from app.orchestrator.llm_router import LLMRouter

logger = logging.getLogger(__name__)


def reflection_agent(state: AgentState):

    llm = LLMRouter.get_llm("reflection")

    prompt = f"""
You are reviewing the final answer.

Question:
{state.question}

SQL:
{state.validated_sql}

Explanation:
{state.explanation}

Decide if the answer is correct.

Return:

VALID
or
RETRY
"""

    response = llm.invoke(prompt)

    decision = response.content.strip().upper()

    if "RETRY" in decision:
        state.status = "REFLECTION_RETRY"
    else:
        state.status = "REFLECTION_OK"

    logger.info({
        "execution_id": state.execution_id,
        "agent": "reflection",
        "status": state.status
    })

    state.history.append("REFLECTION_AGENT")

    return state

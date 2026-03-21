import logging

from app.state.agent_state import AgentState
from app.orchestrator.llm_router import LLMRouter

logger = logging.getLogger(__name__)


def validator_agent(state: AgentState):

    llm = LLMRouter.get_llm("validator")

    prompt = f"""
You are a SQL validation expert.

Question:
{state.question}

SQL:
{state.generated_sql}

Check:
- valid tables
- valid columns
- logical joins
- no destructive operations

Respond only with:

VALID
or
INVALID
"""

    response = llm.invoke(prompt)

    decision = response.content.strip().upper()

    if "INVALID" in decision:
        state.validation_status = "INVALID"
        state.status = "INVALID_SQL"
    else:
        state.validation_status = "VALID"
        state.validated_sql = state.generated_sql
        state.status = "VALID_SQL"

    logger.info({
        "execution_id": state.execution_id,
        "agent": "validator",
        "validation_status": state.validation_status
    })

    state.history.append("VALIDATOR_AGENT")

    return state

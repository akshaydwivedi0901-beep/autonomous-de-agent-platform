import logging

from app.state.agent_state import AgentState
from app.orchestrator.llm_router import LLMRouter

logger = logging.getLogger(__name__)


def sql_agent(state: AgentState):

    llm = LLMRouter.get_llm("sql", state.question)

    prompt = f"""
You are a SQL expert.

Business analysis:
{state.business_analysis}

Generate Snowflake SQL to answer the question.

Return ONLY SQL.
"""

    response = llm.invoke(prompt)

    sql = response.content.strip()

    state.generated_sql = sql
    state.status = "SQL_GENERATED"

    logger.info({
        "execution_id": state.execution_id,
        "agent": "sql",
        "sql": sql
    })

    state.history.append("SQL_AGENT")

    return state

import logging
from app.state.agent_state import AgentState

logger = logging.getLogger(__name__)


def router_agent(state: AgentState):

    try:
        logger.info("🔥 ROUTER START")

        q = (state.question or "").lower()

        sql_keywords = [
            "revenue", "sales", "sum", "count",
            "average", "total", "last", "quarter",
            "month", "year", "top"
        ]

        if any(k in q for k in sql_keywords):
            state.route = "SQL"
        else:
            state.route = "SQL"  # default for now

        logger.info(f"✅ Routing decision: {state.route}")

        return state

    except Exception as e:
        logger.error(f"❌ ROUTER FAILED: {str(e)}")
        state.route = "SQL"
        return state
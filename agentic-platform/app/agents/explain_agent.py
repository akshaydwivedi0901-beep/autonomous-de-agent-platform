import logging
from app.state.agent_state import AgentState

logger = logging.getLogger(__name__)


def explain_agent(state: AgentState):

    try:
        logger.info("🔥 EXPLAIN AGENT START")

        result = state.execution_result

        if not result:
            state.final_answer = "No result returned"
            state.status = "EXPLAINED"
            return state

        rows = result.get("rows")

        if not rows:
            state.final_answer = "No data found"
            state.status = "EXPLAINED"
            return state

        first_row = rows[0]

        if isinstance(first_row, (list, tuple)):
            value = first_row[0]
        elif isinstance(first_row, dict):
            value = list(first_row.values())[0]
        else:
            value = first_row

        # =============================
        # 🔥 HANDLE NULL
        # =============================
        if value is None:
            state.final_answer = "No revenue data found for the selected time period"
            state.status = "EXPLAINED"
            return state

        # Format number
        try:
            value = float(value)
            value = f"{value:,.2f}"
        except Exception:
            pass

        state.final_answer = f"Revenue last quarter is: {value}"
        state.status = "EXPLAINED"

        logger.info(f"✅ FINAL ANSWER: {state.final_answer}")

        return state

    except Exception as e:
        logger.exception(f"❌ EXPLAIN AGENT FAILED: {str(e)}")

        state.final_answer = "Error generating explanation"
        state.error = str(e)
        state.status = "EXPLAIN_FAILED"

        return state
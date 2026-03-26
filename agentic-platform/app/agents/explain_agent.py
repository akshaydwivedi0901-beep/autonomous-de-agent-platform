import logging
from app.state.agent_state import AgentState

logger = logging.getLogger(__name__)


def explain_agent(state: AgentState):

    try:
        logger.info("🔥 EXPLAIN AGENT START")

        rows = state.rows

        if not rows:
            state.final_answer = "No data found"
            state.status = "EXPLAINED"
            return state

        first_row = rows[0]

        # =============================
        # ✅ CASE 1: dict rows (best case)
        # =============================
        if isinstance(first_row, dict):

            if len(first_row) == 1:
                value = list(first_row.values())[0]
                state.final_answer = f"Result is: {value}"
            else:
                lines = ["Customer Details:\n"]
                for k, v in first_row.items():
                    lines.append(f"{k}: {v}")
                state.final_answer = "\n".join(lines)

        # =============================
        # ✅ CASE 2: tuple rows (Snowflake default)
        # =============================
        elif isinstance(first_row, (list, tuple)):

            # If only 1 column
            if len(first_row) == 1:
                state.final_answer = f"Result is: {first_row[0]}"
            else:
                # fallback generic
                values = [str(v) for v in first_row]
                state.final_answer = " | ".join(values)

        else:
            state.final_answer = str(first_row)

        state.status = "EXPLAINED"

        logger.info(f"✅ FINAL ANSWER: {state.final_answer}")

        return state

    except Exception as e:
        logger.exception("❌ EXPLAIN AGENT FAILED")

        state.error = str(e)
        state.status = "EXPLAIN_FAILED"

        return state
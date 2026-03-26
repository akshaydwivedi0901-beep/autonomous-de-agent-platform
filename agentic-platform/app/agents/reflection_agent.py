import logging
from app.state.agent_state import AgentState

logger = logging.getLogger(__name__)


def reflection_agent(state: AgentState) -> AgentState:
    logger.info("🔥 REFLECTION AGENT START")

    # 🔥 STOP CONDITION (MOST IMPORTANT FIX)
    if state.retry_count >= state.max_retries:
        logger.error("❌ Max retries reached. Stopping loop.")

        state.final_answer = "❌ Failed to execute query after multiple attempts."
        state.status = "FAILED"

        return state

    # 🔥 increment retry
    state.retry_count += 1

    logger.warning(f"Retry attempt {state.retry_count}")

    # Send back to SQL
    state.status = "RETRY"

    return state
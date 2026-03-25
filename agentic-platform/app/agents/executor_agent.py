import logging
from app.services.snowflake_service import SnowflakeService
from app.state.agent_state import AgentState

logger = logging.getLogger(__name__)


def executor_agent(state: AgentState):

    try:
        logger.info("🔥 EXECUTOR AGENT START")

        # =============================
        # ✅ USE VALIDATED SQL (CRITICAL FIX)
        # =============================
        sql = state.validated_sql or state.generated_sql

        if not sql:
            raise ValueError("No SQL available for execution")

        logger.info(f"Executing SQL:\n{sql}")

        # =============================
        # ✅ EXECUTE
        # =============================
        service = SnowflakeService()
        result = service.execute(sql)

        # =============================
        # ✅ STORE RESULT (SAFE)
        # =============================
        state.execution_result = result

        # Optional breakdown
        state.rows = result.get("rows")
        state.row_count = result.get("row_count")
        state.execution_time = result.get("execution_time")

        state.status = "EXECUTED"

        logger.info(f"✅ EXECUTION SUCCESS: rows={state.row_count}")

        return state

    except Exception as e:
        logger.exception(f"❌ EXECUTOR AGENT FAILED: {str(e)}")

        state.error = str(e)
        state.status = "EXECUTION_FAILED"

        return state
import logging
from app.services.snowflake_service import SnowflakeService
from app.state.agent_state import AgentState

logger = logging.getLogger(__name__)


def executor_agent(state: AgentState):

    try:
        logger.info("🔥 EXECUTOR AGENT START")

        sql = state.validated_sql or state.generated_sql

        if not sql:
            raise ValueError("No SQL available for execution")

        # 🔥 REMOVE SEMICOLON
        sql = sql.strip().rstrip(";")

        # 🔥 SAFE LIMIT
        if "limit" not in sql.lower():
            sql = f"{sql} LIMIT 100"

        logger.info(f"Executing SQL:\n{sql}")

        service = SnowflakeService()
        result = service.execute(sql)

        state.execution_result = result
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
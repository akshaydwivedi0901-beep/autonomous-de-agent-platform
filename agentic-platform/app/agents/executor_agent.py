# app/agents/executor_agent.py

from app.services.snowflake_service import SnowflakeService
import logging

logger = logging.getLogger(__name__)


def executor_agent(state):
    service = SnowflakeService()

    try:
        result = service.execute(state.generated_sql)

        state.query_id = result["query_id"]
        state.row_count = result["row_count"]
        state.execution_time = result["execution_time"]
        state.status = "EXECUTED"

        # ✅ Add telemetry here
        logger.info({
            "execution_id": state.execution_id,
            "agent": "executor",
            "query_id": state.query_id,
            "row_count": state.row_count,
            "execution_time": state.execution_time,
            "status": state.status
        })

    except Exception as e:
        state.error = str(e)
        state.status = "FAILED"

        logger.error({
            "execution_id": state.execution_id,
            "agent": "executor",
            "error": state.error,
            "status": state.status
        })

    return state

# app/agents/audit_agent.py

import logging
from app.services.snowflake_service import SnowflakeService

logger = logging.getLogger(__name__)


def audit_agent(state):

    service = SnowflakeService()

    insert_sql = """
    INSERT INTO AGENT_DB.AGENT_AUDIT.QUERY_AUDIT_LOG (
        EXECUTION_ID,
        QUESTION,
        INTENT,
        GENERATED_SQL,
        ROW_COUNT,
        EXECUTION_TIME_SECONDS,
        ERROR,
        RETRY_COUNT,
        QUERY_ID,
        GOVERNANCE_STATUS,
        RISK_SCORE,
        VALIDATION_STATUS,
        ENVIRONMENT,
        STATUS
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        state.execution_id,
        state.question,
        state.intent,
        state.generated_sql,
        state.row_count or 0,
        state.execution_time or 0,
        state.error or "",
        state.retry_count,
        state.query_id or "",
        state.governance_status or "",
        state.risk_score,
        state.validation_status or "",
        state.environment,
        state.status
    )

    try:
        service.execute(insert_sql, values)

        logger.info({
            "execution_id": state.execution_id,
            "agent": "audit",
            "final_status": state.status
        })

    except Exception as e:
        logger.error({
            "execution_id": state.execution_id,
            "agent": "audit",
            "error": str(e)
        })

    return state

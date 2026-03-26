import logging
from app.state.agent_state import AgentState
from app.services.snowflake_service import SnowflakeService

logger = logging.getLogger(__name__)


def audit_agent(state: AgentState):

    try:
        logger.info("🔥 AUDIT AGENT START")

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
            getattr(state, "intent", None),
            state.generated_sql,
            getattr(state, "row_count", 0),
            getattr(state, "execution_time", 0),
            getattr(state, "error", ""),
            state.retry_count,
            getattr(state, "query_id", ""),
            getattr(state, "governance_status", ""),
            getattr(state, "risk_score", 0),
            state.validation_status or "",
            getattr(state, "environment", "DEV"),
            state.status
        )

        service.execute(insert_sql, values)

        logger.info({
            "execution_id": state.execution_id,
            "agent": "audit",
            "final_status": state.status
        })

        # Optional: track in memory
        state.conversation_history.append({
            "role": "system",
            "message": "AUDIT_AGENT completed"
        })

        return state

    except Exception as e:
        logger.error({
            "execution_id": getattr(state, "execution_id", "UNKNOWN"),
            "agent": "audit",
            "error": str(e)
        })

        # ⚠️ IMPORTANT: audit should NEVER break pipeline
        return state
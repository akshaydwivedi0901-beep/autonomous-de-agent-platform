import logging
from app.state.agent_state import AgentState
from app.services.snowflake_service import SnowflakeService

logger = logging.getLogger(__name__)


def audit_agent(state: AgentState):

    try:
        logger.info("🔥 AUDIT AGENT START")

        service = SnowflakeService()

        # =============================
        # ENSURE AUDIT TABLE EXISTS
        # =============================
        create_sql = """
        CREATE TABLE IF NOT EXISTS AGENT_DB.AGENT_AUDIT.QUERY_AUDIT_LOG (
            EXECUTION_ID        VARCHAR,
            QUESTION            VARCHAR,
            INTENT              VARCHAR,
            GENERATED_SQL       VARCHAR,
            ROW_COUNT           NUMBER,
            EXECUTION_TIME_SECONDS FLOAT,
            ERROR               VARCHAR,
            RETRY_COUNT         NUMBER,
            QUERY_ID            VARCHAR,
            GOVERNANCE_STATUS   VARCHAR,
            RISK_SCORE          NUMBER,
            VALIDATION_STATUS   VARCHAR,
            ENVIRONMENT         VARCHAR,
            STATUS              VARCHAR,
            CREATED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
        """

        try:
            service.execute(create_sql)
        except Exception as e:
            logger.warning(f"Audit table creation skipped: {e}")

        # =============================
        # BUILD INSERT WITH INLINE VALUES
        # (Snowflake connector does not support %s parameterized INSERT)
        # =============================
        def safe_str(val):
            if val is None:
                return "NULL"
            return "'" + str(val).replace("'", "''") + "'"

        insert_sql = f"""
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
        VALUES (
            {safe_str(state.execution_id)},
            {safe_str(state.question)},
            {safe_str(getattr(state, 'intent', None))},
            {safe_str(state.generated_sql)},
            {getattr(state, 'row_count', 0) or 0},
            {getattr(state, 'execution_time', 0) or 0},
            {safe_str(getattr(state, 'error', ''))},
            {state.retry_count or 0},
            {safe_str(getattr(state, 'query_id', ''))},
            {safe_str(getattr(state, 'governance_status', ''))},
            {getattr(state, 'risk_score', 0) or 0},
            {safe_str(state.validation_status or '')},
            {safe_str(getattr(state, 'environment', 'DEV'))},
            {safe_str(state.status)}
        )
        """

        service.execute(insert_sql)

        logger.info({
            "execution_id": state.execution_id,
            "agent": "audit",
            "final_status": state.status
        })

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

        # ⚠️ Audit should NEVER break the pipeline
        return state
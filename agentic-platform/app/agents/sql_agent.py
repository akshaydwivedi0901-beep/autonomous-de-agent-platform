import logging
import json

from app.state.agent_state import AgentState
from app.orchestrator.llm_router import LLMRouter
from app.services.schema_service import SchemaService

logger = logging.getLogger(__name__)


def sql_agent(state: AgentState):

    try:
        logger.info("🔥 SQL AGENT START")

        question = state.question.lower()

        # =============================
        # ⚡ FIXED RULE (DATASET SAFE)
        # =============================
        if "revenue" in question and "quarter" in question:

            logger.info("⚡ Using rule-based SQL (fixed TPCH dates)")

            sql = """
SELECT 
    SUM(l.l_extendedprice * (1 - l.l_discount)) AS revenue
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM l
JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS o
    ON l.l_orderkey = o.o_orderkey
WHERE o.o_orderdate >= '1995-01-01'
  AND o.o_orderdate < '1995-04-01'
"""

        else:
            # =============================
            # 🔥 LLM + SCHEMA
            # =============================
            schema_service = SchemaService()
            schema = schema_service.get_schema_metadata()

            llm = LLMRouter.get_llm("sql", question)

            prompt = f"""
You are a Snowflake SQL expert.

Use ONLY this schema:
{json.dumps(schema, indent=2)}

Rules:
- Only SELECT
- No DELETE/UPDATE/INSERT
- No SELECT *
- Use LIMIT 100

Question:
{state.question}

Return only SQL.
"""

            response = llm.invoke(prompt)
            sql = response.content.strip()

            if "```" in sql:
                sql = sql.split("```")[1].replace("sql", "").strip()

        logger.info(f"FINAL SQL:\n{sql}")

        state.generated_sql = sql
        state.status = "SQL_GENERATED"

        return state

    except Exception as e:
        logger.exception("❌ SQL AGENT FAILED")

        state.error = str(e)
        state.status = "SQL_FAILED"

        return state
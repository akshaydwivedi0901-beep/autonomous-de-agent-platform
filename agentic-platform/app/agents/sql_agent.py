import logging
import re

from app.state.agent_state import AgentState
from app.services.schema_service import SchemaService
from app.orchestrator.llm_router import LLMRouter

logger = logging.getLogger(__name__)

# =========================================
# PROMPT TEMPLATE
# =========================================
SQL_PROMPT = """You are an expert Snowflake SQL generator for a data analytics platform.

STRICT RULES:
- Return ONLY the raw SQL query. No markdown, no backticks, no explanation.
- Use fully-qualified table names: SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.<TABLE>
- Never use SELECT *. Always name specific columns.
- Always add a WHERE clause when filtering is possible.
- Never use DROP, DELETE, UPDATE, INSERT, TRUNCATE, ALTER.
- Query must start with SELECT or WITH.

DATABASE SCHEMA:
{schema}

CONVERSATION HISTORY (last 5 turns):
{history}

RELEVANT KNOWLEDGE (from RAG):
{rag_context}

USER QUESTION:
{question}

SQL QUERY:"""


def _format_schema(schema: dict) -> str:
    lines = []
    for table, cols in schema.items():
        if isinstance(cols, list):
            col_names = ", ".join(c["column"] for c in cols[:15])
        else:
            col_names = str(cols)
        lines.append(f"  {table}: {col_names}")
    return "\n".join(lines)


def _format_history(history: list) -> str:
    if not history:
        return "None"
    return "\n".join(
        f"  {m.get('role', 'user').upper()}: {m.get('message', '')}"
        for m in history[-5:]
    )


def _clean_sql(raw: str) -> str:
    """Strip markdown fences, leading/trailing whitespace, and trailing semicolons."""
    sql = re.sub(r"```sql|```", "", raw)
    sql = sql.strip().rstrip(";")
    return sql


# =========================================
# AGENT
# =========================================
def sql_agent(state: AgentState) -> AgentState:

    try:
        logger.info(" SQL AGENT START (LLM-powered)")

        # =============================
        # FETCH SCHEMA (cached per process via service)
        # =============================
        try:
            schema_service = SchemaService()
            schema = schema_service.get_schema_metadata()
            schema_text = _format_schema(schema)
        except Exception as e:
            logger.warning(f"Schema fetch failed, using fallback: {e}")
            schema_text = (
                "CUSTOMER: C_CUSTKEY, C_NAME, C_ADDRESS, C_PHONE, C_ACCTBAL, C_MKTSEGMENT\n"
                "ORDERS: O_ORDERKEY, O_CUSTKEY, O_TOTALPRICE, O_ORDERDATE, O_ORDERSTATUS\n"
                "LINEITEM: L_ORDERKEY, L_PARTKEY, L_SUPPKEY, L_QUANTITY, L_EXTENDEDPRICE\n"
                "PART: P_PARTKEY, P_NAME, P_TYPE, P_SIZE, P_RETAILPRICE\n"
                "SUPPLIER: S_SUPPKEY, S_NAME, S_ADDRESS, S_NATIONKEY, S_ACCTBAL\n"
                "NATION: N_NATIONKEY, N_NAME, N_REGIONKEY\n"
                "REGION: R_REGIONKEY, R_NAME"
            )

        # =============================
        # BUILD PROMPT
        # =============================
        prompt = SQL_PROMPT.format(
            schema=schema_text,
            history=_format_history(state.conversation_history),
            rag_context=state.rag_context or "None",
            question=state.question,
        )

        # =============================
        # LLM CALL (large model for SQL)
        # =============================
        llm = LLMRouter.get_llm("sql", state.question)
        response = llm.invoke(prompt)
        raw_sql = response.content.strip()

        sql = _clean_sql(raw_sql)

        if not sql.upper().startswith(("SELECT", "WITH")):
            raise ValueError(f"LLM returned non-SELECT output: {sql[:100]}")

        state.generated_sql = sql
        state.status = "SQL_GENERATED"

        logger.info(f" LLM-generated SQL:\n{sql}")

        return state

    except Exception as e:
        logger.exception(" SQL AGENT FAILED")
        state.error = str(e)
        state.status = "SQL_FAILED"
        return state
import logging

from app.state.agent_state import AgentState

logger = logging.getLogger(__name__)


# =========================================
# 🔥 CONFIG
# =========================================
ALLOWED_TABLES = {
    "CUSTOMER", "ORDERS", "LINEITEM",
    "PART", "SUPPLIER", "REGION", "NATION"
}

FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE",
    "UPDATE", "INSERT", "ALTER"
]


# =========================================
# 🔥 HELPERS
# =========================================
def contains_forbidden(sql: str) -> bool:
    sql_upper = sql.upper()
    return any(k in sql_upper for k in FORBIDDEN_KEYWORDS)


def is_select_query(sql: str) -> bool:
    sql_upper = sql.strip().upper()
    return sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")


def contains_allowed_table(sql: str) -> bool:
    sql_upper = sql.upper()
    return any(table in sql_upper for table in ALLOWED_TABLES)


def has_select_star(sql: str) -> bool:
    return "SELECT *" in sql.upper()


# =========================================
# 🔥 FIXED LIMIT HANDLER (CRITICAL FIX)
# =========================================
def enforce_limit(sql: str) -> str:
    sql = sql.strip()

    # ✅ Remove trailing semicolon (fix for Snowflake error)
    if sql.endswith(";"):
        sql = sql[:-1]

    # ✅ Add LIMIT only if not present
    if "LIMIT" not in sql.upper():
        sql += "\nLIMIT 100"

    return sql


# =========================================
# 🔥 MAIN VALIDATOR
# =========================================
def validator_agent(state: AgentState):

    try:
        logger.info("🔥 VALIDATOR START")

        sql = state.generated_sql

        # =============================
        # Basic checks
        # =============================
        if not sql or not sql.strip():
            raise ValueError("No SQL generated")

        sql = sql.strip()

        # =============================
        # 🚫 Dangerous SQL
        # =============================
        if contains_forbidden(sql):
            state.validation_status = "INVALID"
            state.status = "INVALID_SQL"
            state.error = "Dangerous SQL detected"
            return state

        # =============================
        # ✅ Must be SELECT
        # =============================
        if not is_select_query(sql):
            state.validation_status = "INVALID"
            state.status = "INVALID_SQL"
            state.error = "Only SELECT queries allowed"
            return state

        # =============================
        # ✅ Must use known tables
        # =============================
        if not contains_allowed_table(sql):
            state.validation_status = "INVALID"
            state.status = "INVALID_SQL"
            state.error = "No allowed table used"
            return state

        # =============================
        # 🚫 No SELECT *
        # =============================
        if has_select_star(sql):
            state.validation_status = "INVALID"
            state.status = "INVALID_SQL"
            state.error = "SELECT * is not allowed"
            return state

        # =============================
        # 💰 Cost control (FIXED)
        # =============================
        sql = enforce_limit(sql)

        # =============================
        # ✅ SUCCESS
        # =============================
        state.validation_status = "VALID"
        state.validated_sql = sql
        state.status = "VALID_SQL"

        logger.info("✅ SQL VALIDATION PASSED")

        return state

    except Exception as e:
        logger.exception("❌ VALIDATOR FAILED")

        state.validation_status = "INVALID"
        state.status = "VALIDATOR_FAILED"
        state.error = str(e)

        return state
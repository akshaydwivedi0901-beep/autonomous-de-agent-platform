import logging
import re
from app.state.agent_state import AgentState
from app.services.schema_service import SchemaService

logger = logging.getLogger(__name__)


def sql_agent(state: AgentState):

    try:
        logger.info("🔥 SQL AGENT START")

        question = state.question.lower()

        schema_service = SchemaService()
        schema = schema_service.get_schema_metadata()

        logger.info(f"Available tables: {list(schema.keys())}")

        # =============================
        # CUSTOMER DETAILS
        # =============================
        if "customer" in question:

            match = re.search(r"\d+", question)
            if not match:
                raise ValueError("Customer ID not found")

            cust_id = match.group()

            logger.info(f"Fetching FULL details for customer {cust_id}")

            # 🔥 ALWAYS SELECT FULL CUSTOMER PROFILE
            sql = f"""
            SELECT 
                C_CUSTKEY,
                C_NAME,
                C_ADDRESS,
                C_PHONE,
                C_ACCTBAL,
                C_MKTSEGMENT,
                C_NATIONKEY
            FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER
            WHERE C_CUSTKEY = {cust_id}
            """

        # =============================
        # ORDER COUNT
        # =============================
        elif "how many orders" in question:

            sql = """
            SELECT COUNT(*) AS total_orders
            FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
            WHERE O_ORDERDATE >= '1995-01-01'
              AND O_ORDERDATE < '1995-04-01'
            """

        else:
            raise ValueError("Unsupported query")

        # =============================
        # CLEAN SQL
        # =============================
        sql = sql.strip().rstrip(";")

        state.generated_sql = sql

        logger.info(f"FINAL SQL:\n{sql}")

        return state

    except Exception as e:
        logger.exception("❌ SQL AGENT FAILED")

        state.error = str(e)
        state.status = "SQL_FAILED"

        return state
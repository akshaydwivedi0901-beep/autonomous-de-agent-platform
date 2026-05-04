import snowflake.connector
import time
import logging
from app.core.config import Settings

logger = logging.getLogger(__name__)


class SnowflakeService:

    def _connect(self):
        return snowflake.connector.connect(**Settings.SNOWFLAKE_CONFIG)

    def execute(self, sql: str):
        conn = self._connect()
        cursor = conn.cursor()

        try:
            #  SET CONTEXT
            cursor.execute("USE DATABASE SNOWFLAKE_SAMPLE_DATA")
            cursor.execute("USE SCHEMA TPCH_SF1")

            start = time.time()

            cursor.execute(sql)
            rows = cursor.fetchall()

            execution_time = time.time() - start

            return {
                "rows": rows,
                "row_count": len(rows),
                "query_id": cursor.sfqid,
                "execution_time": execution_time
            }

        finally:
            cursor.close()
            conn.close()
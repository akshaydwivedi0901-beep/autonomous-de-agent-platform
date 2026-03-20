# app/services/snowflake_service.py

import snowflake.connector
import time
from app.core.config import Settings

class SnowflakeService:

    def _connect(self):
        return snowflake.connector.connect(**Settings.SNOWFLAKE_CONFIG)

    def execute(self, sql: str, params=None):
        conn = self._connect()
        cursor = conn.cursor()

        try:
            start = time.time()

            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            try:
                rows = cursor.fetchall()
            except:
                rows = []

            query_id = cursor.sfqid
            execution_time = time.time() - start

            return {
                "rows": rows,
                "query_id": query_id,
                "row_count": len(rows),
                "execution_time": execution_time
            }

        finally:
            cursor.close()
            conn.close()
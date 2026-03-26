import snowflake.connector
from app.core.config import Settings


class SchemaService:

    def get_schema_metadata(self):

        conn = snowflake.connector.connect(**Settings.SNOWFLAKE_CONFIG)
        cursor = conn.cursor()

        try:
            # 🔥 HARD FIX: use explicit DB + SCHEMA
            cursor.execute("""
                SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
                FROM SNOWFLAKE_SAMPLE_DATA.INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'TPCH_SF1'
            """)

            columns = cursor.fetchall()

            schema = {}

            for table, column, dtype in columns:
                if table not in schema:
                    schema[table] = []

                schema[table].append({
                    "column": column,
                    "type": dtype
                })

            return schema

        finally:
            cursor.close()
            conn.close()
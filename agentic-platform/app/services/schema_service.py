import snowflake.connector
from app.core.config import Settings


class SchemaService:

    def get_schema_metadata(self):
        conn = snowflake.connector.connect(**Settings.SNOWFLAKE_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
        """)

        columns = cursor.fetchall()

        cursor.execute("""
            SELECT *
            FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS
        """)

        fks = cursor.fetchall()

        cursor.close()
        conn.close()

        schema = {}
        for table, column, dtype in columns:
            schema.setdefault(table, []).append({
                "column": column,
                "type": dtype
            })

        return {
            "tables": schema,
            "foreign_keys": fks
        }

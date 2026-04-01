import logging
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Dict, List

from app.core.config import settings

logger = logging.getLogger(__name__)


# =========================================
# ABSTRACT BASE
# =========================================
class BaseSchemaService(ABC):

    @abstractmethod
    def get_schema_metadata(self) -> Dict[str, List]:
        pass


# =========================================
# SNOWFLAKE
# =========================================
class SnowflakeSchemaService(BaseSchemaService):

    def get_schema_metadata(self) -> Dict:
        import snowflake.connector

        conn = snowflake.connector.connect(**settings.SNOWFLAKE_CONFIG)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
                FROM SNOWFLAKE_SAMPLE_DATA.INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'TPCH_SF1'
                ORDER BY TABLE_NAME, ORDINAL_POSITION
            """)

            schema: Dict[str, List] = {}

            for table, column, dtype in cursor.fetchall():
                schema.setdefault(table, []).append({
                    "column": column,
                    "type": dtype,
                })

            logger.info(f"Snowflake schema loaded: {list(schema.keys())}")
            return schema

        finally:
            cursor.close()
            conn.close()


# =========================================
# POSTGRES
# =========================================
class PostgresSchemaService(BaseSchemaService):

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def get_schema_metadata(self) -> Dict:
        import psycopg2

        conn = psycopg2.connect(self.connection_string)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)

            schema: Dict[str, List] = {}

            for table, column, dtype in cursor.fetchall():
                schema.setdefault(table, []).append({
                    "column": column,
                    "type": dtype,
                })

            logger.info(f"Postgres schema loaded: {list(schema.keys())}")
            return schema

        finally:
            cursor.close()
            conn.close()


# =========================================
# BIGQUERY
# =========================================
class BigQuerySchemaService(BaseSchemaService):

    def __init__(self, project: str, dataset: str):
        self.project = project
        self.dataset = dataset

    def get_schema_metadata(self) -> Dict:
        from google.cloud import bigquery

        client = bigquery.Client(project=self.project)
        schema: Dict[str, List] = {}

        for table_ref in client.list_tables(self.dataset):
            table = client.get_table(table_ref)
            schema[table.table_id] = [
                {"column": f.name, "type": str(f.field_type)}
                for f in table.schema
            ]

        logger.info(f"BigQuery schema loaded: {list(schema.keys())}")
        return schema


# =========================================
# MYSQL / MARIADB
# =========================================
class MySQLSchemaService(BaseSchemaService):

    def __init__(self, host: str, user: str, password: str, database: str):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def get_schema_metadata(self) -> Dict:
        import mysql.connector

        conn = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
        )
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME, ORDINAL_POSITION
            """, (self.database,))

            schema: Dict[str, List] = {}

            for table, column, dtype in cursor.fetchall():
                schema.setdefault(table, []).append({
                    "column": column,
                    "type": dtype,
                })

            return schema

        finally:
            cursor.close()
            conn.close()


# =========================================
# FACTORY — Auto-selects based on DB_TYPE
# =========================================
class SchemaService:
    """
    Factory that selects the correct schema service at runtime.

    Set DB_TYPE env var to: snowflake | postgres | bigquery | mysql
    """

    _instance: BaseSchemaService = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._service = cls._build_service()
        return cls._instance

    @staticmethod
    def _build_service() -> BaseSchemaService:
        db_type = getattr(settings, "DB_TYPE", "snowflake").lower()

        logger.info(f"Initialising SchemaService for DB_TYPE={db_type}")

        if db_type == "snowflake":
            return SnowflakeSchemaService()

        if db_type == "postgres":
            return PostgresSchemaService(settings.POSTGRES_URL)

        if db_type == "bigquery":
            return BigQuerySchemaService(
                settings.BIGQUERY_PROJECT,
                settings.BIGQUERY_DATASET,
            )

        if db_type == "mysql":
            return MySQLSchemaService(
                host=settings.MYSQL_HOST,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                database=settings.MYSQL_DATABASE,
            )

        raise ValueError(
            f"Unsupported DB_TYPE '{db_type}'. "
            "Choose from: snowflake, postgres, bigquery, mysql"
        )

    def get_schema_metadata(self) -> Dict:
        return self._service.get_schema_metadata()
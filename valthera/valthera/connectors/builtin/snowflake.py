import os
from typing import Callable, Dict, Any, Optional
import snowflake.connector
from valthera.connectors.generic_sql_connector import GenericSQLConnector


class SnowflakeSQLConnector(GenericSQLConnector):
    """
    A connector for Snowflake that executes SQL queries using Snowflake's Python connector.
    Environment variables required:
      - SNOWFLAKE_USER
      - SNOWFLAKE_PASSWORD
      - SNOWFLAKE_ACCOUNT
      - SNOWFLAKE_WAREHOUSE
      - SNOWFLAKE_DATABASE
      - SNOWFLAKE_SCHEMA
    """
    def __init__(
        self,
        table_name: str,
        query_builder: Optional[Callable[[str, str], str]] = None,
        row_parser: Optional[Callable[[str, tuple], Dict[str, Any]]] = None,
        user_field: str = "USER_ID"
    ):
        # Initialize the generic SQL connector from the valthera package.
        super().__init__(table_name, query_builder, row_parser, user_field)

        # Retrieve Snowflake connection settings from environment variables.
        self.user = os.getenv("SNOWFLAKE_USER")
        self.password = os.getenv("SNOWFLAKE_PASSWORD")
        self.account = os.getenv("SNOWFLAKE_ACCOUNT")
        self.warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        self.database = os.getenv("SNOWFLAKE_DATABASE")
        self.schema = os.getenv("SNOWFLAKE_SCHEMA")

        required_vars = [self.user, self.password, self.account, self.warehouse, self.database, self.schema]
        if not all(required_vars):
            raise ValueError("Missing one or more Snowflake environment variables.")

    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        try:
            # Establish the Snowflake connection.
            ctx = snowflake.connector.connect(
                user=self.user,
                password=self.password,
                account=self.account,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema
            )
            cs = ctx.cursor()
            try:
                query = self.query_builder(user_id, self.table_name)
                cs.execute(query)
                row = cs.fetchone()
                if row:
                    return self.row_parser(user_id, row)
                return {}
            finally:
                cs.close()
                ctx.close()
        except snowflake.connector.Error as sf_err:
            print(f"Snowflake error: {sf_err}")
        except Exception as ex:
            print(f"Unexpected error in SnowflakeSQLConnector for user {user_id}: {ex}")
        return {}

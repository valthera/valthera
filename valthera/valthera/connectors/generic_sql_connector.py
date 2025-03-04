import os
import psycopg2
import psycopg2.extras
from typing import Any, Callable, Dict, Optional
from valthera.connectors.base_connector import BaseConnector


def default_query_builder(user_id: str, table_name: str, user_field: str = "USER_ID") -> str:
    """
    Builds a basic SQL query given the table name and user identifier field.
    """
    return f"""
    SELECT *
    FROM {table_name}
    WHERE {user_field} = '{user_id}'
    """


class GenericSQLConnector(BaseConnector):
    """
    A connector that uses a configurable query builder and row parser.
    """

    def __init__(
        self,
        table_name: str,
        query_builder: Optional[Callable[[str, str], str]] = None,
        row_parser: Optional[Callable[[str, tuple], Dict[str, Any]]] = None,
        user_field: str = "USER_ID"
    ):
        self.user = os.getenv("POSTGRES_USER")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.database = os.getenv("POSTGRES_DB")

        required_vars = [self.user, self.password, self.host, self.port, self.database]
        if not all(required_vars):
            raise ValueError("Missing one or more Postgres environment variables.")

        self.table_name = table_name
        self.user_field = user_field
        self.query_builder = query_builder if query_builder else default_query_builder
        self.row_parser = row_parser if row_parser else self.default_row_parser

    def get_user_data(self, user_id: str) -> Dict[str, Any]:
        try:
            with psycopg2.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database
            ) as conn:
                with conn.cursor() as cur:
                    query = self.query_builder(user_id, self.table_name)
                    cur.execute(query)
                    row = cur.fetchone()
                    if row:
                        return self.row_parser(user_id, row)
                    return {}
        except psycopg2.Error as pg_err:
            print(f"Postgres error: {pg_err}")
        except Exception as ex:
            print(f"Unexpected error in GenericSQLConnector for user {user_id}: {ex}")

        return {}

    def default_row_parser(self, user_id: str, row: tuple) -> Dict[str, Any]:
        """
        A very basic row parser that returns the row as a dict with indices as keys.
        In practice, you'd map columns to more meaningful names.
        """
        return {"user_id": user_id, **{f"field_{i}": value for i, value in enumerate(row)}}

import re
import polars as pl
from clickhouse_connect import get_client
from attribution.base_connector import BaseConnector

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ClickHouseConnector(BaseConnector):
    """Reads events from a ClickHouse database."""

    def fetch(self, start_date: str = None, end_date: str = None) -> pl.DataFrame:
        client = get_client(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 8123),
            username=self.config.get("user", "default"),
            password=self.config.get("password", ""),
        )

        query = self.config.get("query")
        query_params = {}

        if not query:
            table = self.config.get("table", "events")
            if not _SAFE_IDENTIFIER.match(table):
                raise ValueError(f"Invalid table name: {table!r}")

            query = f"SELECT * FROM {table}"
            if start_date and end_date:
                query += " WHERE timestamp BETWEEN {start_date:String} AND {end_date:String}"
                query_params = {"start_date": start_date, "end_date": end_date}

        result = client.query(query, parameters=query_params)
        df = pl.DataFrame(result.result_rows, schema=result.column_names, orient="row")
        df = self._cast_revenue(df)
        return df
    
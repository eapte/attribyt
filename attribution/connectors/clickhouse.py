import polars as pl
from clickhouse_connect import get_client
from attribution.base_connector import BaseConnector

class ClickHouseConnector(BaseConnector):
    def fetch(self, start_date: str = None, end_date: str = None) -> pl.DataFrame:
        client = get_client(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", 8123),
            username=self.config.get("user", "default"),
            password=self.config.get("password", ""),
        )
        query = self.config.get("query")
        if not query:
            table = self.config.get("table", "events")
            query = f"SELECT * FROM {table}"
        if start_date and end_date:
            query += f" WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'"
        result = client.query(query)
        df = pl.DataFrame(result.result_rows, schema=result.column_names)
        df = df.with_columns(pl.col("revenue").cast(pl.Float64, strict=False))
        return df
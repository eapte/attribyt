import polars as pl
from sqlalchemy import create_engine
from attribution.base_connector import BaseConnector

class PostgresConnector(BaseConnector):
    def fetch(self, start_date: str = None, end_date: str = None) -> pl.DataFrame:
        dsn = self.config.get("dsn")
        query = self.config.get("query")
        if not query:
            table = self.config.get("table", "events")
            query = f"SELECT * FROM {table}"
        if start_date and end_date:
            query += f" WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'"
        engine = create_engine(dsn)
        with engine.connect() as conn:
            df = pl.read_database(query, conn)
        df = df.with_columns(pl.col("revenue").cast(pl.Float64, strict=False))
        return df
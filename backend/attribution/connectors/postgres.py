import re
import polars as pl
from sqlalchemy import create_engine, text
from attribution.base_connector import BaseConnector

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class PostgresConnector(BaseConnector):
    """Reads events from a PostgreSQL database."""

    def fetch(self, start_date: str = None, end_date: str = None) -> pl.DataFrame:
        dsn = self.config.get("dsn")
        if not dsn:
            raise ValueError("PostgresConnector requires 'dsn' in config")

        query = self.config.get("query")
        params = {}

        if not query:
            table = self.config.get("table", "events")
            if not _SAFE_IDENTIFIER.match(table):
                raise ValueError(f"Invalid table name: {table!r}")

            query = f"SELECT * FROM {table}"
            if start_date and end_date:
                query += " WHERE timestamp BETWEEN :start_date AND :end_date"
                params = {"start_date": start_date, "end_date": end_date}

        engine = create_engine(dsn)
        with engine.connect() as conn:
            df = pl.read_database(text(query).bindparams(**params) if params else text(query), conn)

        df = self._cast_revenue(df)
        return df
    
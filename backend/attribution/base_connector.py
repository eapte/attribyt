from abc import ABC, abstractmethod
import polars as pl


class BaseConnector(ABC):
    """Base class for all data source connectors."""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def fetch(self, start_date: str = None, end_date: str = None) -> pl.DataFrame:
        """Fetch raw event data from the source."""
        raise NotImplementedError

    @staticmethod
    def _cast_revenue(df: pl.DataFrame, column: str = "revenue") -> pl.DataFrame:
        """Ensure the revenue column is numeric across all connectors."""
        if column in df.columns:
            df = df.with_columns(pl.col(column).cast(pl.Float64, strict=False))
        return df
    
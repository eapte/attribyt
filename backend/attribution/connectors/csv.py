import polars as pl
from attribution.base_connector import BaseConnector


class CSVConnector(BaseConnector):
    """Reads events from a local CSV file."""

    def fetch(self, start_date: str = None, end_date: str = None) -> pl.DataFrame:
        file_path = self.config.get("file_path")
        if not file_path:
            raise ValueError("CSVConnector requires 'file_path' in config")

        df = pl.read_csv(file_path)
        df = self._cast_revenue(df)

        if start_date and end_date and "timestamp" in df.columns:
            df = df.filter(
                (pl.col("timestamp") >= start_date) & (pl.col("timestamp") <= end_date)
            )

        return df
    
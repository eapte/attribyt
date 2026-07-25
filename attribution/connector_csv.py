import polars as pl
from attribution.base_connector import BaseConnector

class CSVConnector(BaseConnector):
    def fetch(self, start_date: str = None, end_date: str = None) -> pl.DataFrame:
        df = pl.read_csv(self.config["file_path"])
        return df
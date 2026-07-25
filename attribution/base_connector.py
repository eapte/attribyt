from abc import ABC, abstractmethod
import polars as pl

class BaseConnector(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def fetch(self, start_date: str, end_date: str) -> pl.DataFrame:
        pass
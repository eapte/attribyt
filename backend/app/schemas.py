from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    model: str = "both"
    user_col: str = "user_id"
    timestamp_col: str = "timestamp"
    channel_col: str = "channel"
    event_col: str = "event_type"
    revenue_col: str = "revenue"
    start_date: str | None = None
    end_date: str | None = None


class SummaryOut(BaseModel):
    total_users: int
    total_touches: int
    conversion_users: int
    non_conversion_users: int
    conversion_rate: float
    avg_revenue_per_converting_user: float
    total_revenue: float


class ChannelComparisonOut(BaseModel):
    channel: str
    last_click: float | None = None
    linear: float | None = None
    time_decay: float | None = None
    markov: float | None = None


class TopPathOut(BaseModel):
    path: str
    count: int
    revenue: float


class AnalyzeResponse(BaseModel):
    summary: SummaryOut
    comparison: list[ChannelComparisonOut]
    top_paths: list[TopPathOut]
    data_quality: dict
    
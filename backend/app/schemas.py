from pydantic import BaseModel


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


class SegmentBreakdownOut(BaseModel):
    segment: str
    count: int
    revenue: float


class AnalyzeResponse(BaseModel):
    summary: SummaryOut
    comparison: list[ChannelComparisonOut]
    top_paths: list[TopPathOut]
    segment_breakdown: list[SegmentBreakdownOut]
    data_quality: dict 
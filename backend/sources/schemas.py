from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .models import SourceType, SyncMode


class SourceCreate(BaseModel):
    """Payload for creating a new source via the API."""
    type: SourceType
    name: str
    credentials: dict = {}
    sync_mode: SyncMode = SyncMode.MANUAL


class SourceResponse(BaseModel):
    """Public representation of a source returned by the API.
    Credentials are intentionally excluded from the response."""
    id: str
    type: SourceType
    name: str
    sync_mode: SyncMode
    status: str
    last_error: Optional[str] = None
    cursor: Optional[str] = None
    last_sync: Optional[datetime] = None
    created_at: datetime


class SourceAnalyzeRequest(BaseModel):
    """Column mapping for running analysis on a source's synced data —
    mirrors the mapping used for file uploads, since a source's raw
    columns rarely match Attribyt's standard names."""
    user_col: str
    timestamp_col: str
    channel_col: str
    revenue_col: str
    segment_col: Optional[str] = None
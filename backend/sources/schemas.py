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
    cursor: Optional[str] = None
    last_sync: Optional[datetime] = None
    created_at: datetime 
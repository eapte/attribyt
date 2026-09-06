from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class SourceType(str, Enum):
    """Types of external data sources Attribyt can connect to."""
    DATABASE = "database"
    REST_API = "rest_api"
    WEBHOOK = "webhook"


class SyncMode(str, Enum):
    """How data gets pulled from the source."""
    MANUAL = "manual"
    POLLING = "polling"
    WEBHOOK = "webhook"


@dataclass
class Source:
    """Represents a connected external data source."""
    type: SourceType
    name: str
    credentials: dict = field(default_factory=dict)  # will be encrypted later
    sync_mode: SyncMode = SyncMode.MANUAL
    cursor: Optional[str] = None
    last_sync: Optional[datetime] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "disconnected"  # disconnected | connected | pending | error
    last_error: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize the source to a JSON-friendly dict."""
        d = self.__dict__.copy()
        d["type"] = self.type.value
        d["sync_mode"] = self.sync_mode.value
        d["created_at"] = self.created_at.isoformat()
        d["last_sync"] = self.last_sync.isoformat() if self.last_sync else None
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Source":
        """Rebuild a Source object from a stored dict."""
        d = d.copy()
        d["type"] = SourceType(d["type"])
        d["sync_mode"] = SyncMode(d["sync_mode"])
        d["created_at"] = datetime.fromisoformat(d["created_at"])
        d["last_sync"] = datetime.fromisoformat(d["last_sync"]) if d.get("last_sync") else None
        d.setdefault("last_error", None)
        return cls(**d) 
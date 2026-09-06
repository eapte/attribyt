import json
from pathlib import Path
from typing import List, Optional
from .models import Source

# Temporary JSON-file storage. Will be replaced with a real DB later,
# but the interface below (list/get/create/delete/update_status)
# stays the same so callers won't need to change.
STORAGE_PATH = Path(__file__).parent / "sources_data.json"


class SourceService:
    """Handles reading and writing Source records."""

    def __init__(self, storage_path: Path = STORAGE_PATH):
        self.storage_path = storage_path
        if not self.storage_path.exists():
            self.storage_path.write_text("[]")

    def _load(self) -> List[Source]:
        data = json.loads(self.storage_path.read_text())
        return [Source.from_dict(d) for d in data]

    def _save(self, sources: List[Source]) -> None:
        self.storage_path.write_text(
            json.dumps([s.to_dict() for s in sources], indent=2)
        )

    def list_sources(self) -> List[Source]:
        return self._load()

    def get_source(self, source_id: str) -> Optional[Source]:
        return next((s for s in self._load() if s.id == source_id), None)

    def create_source(self, source: Source) -> Source:
        sources = self._load()
        sources.append(source)
        self._save(sources)
        return source

    def delete_source(self, source_id: str) -> bool:
        sources = self._load()
        filtered = [s for s in sources if s.id != source_id]
        if len(filtered) == len(sources):
            return False
        self._save(filtered)
        return True

    def update_status(self, source_id: str, status: str) -> Optional[Source]:
        sources = self._load()
        for s in sources:
            if s.id == source_id:
                s.status = status
                self._save(sources)
                return s
        return None 
"""Decision memory — structured JSON storage for deliberation results."""

from __future__ import annotations

import json
from pathlib import Path

from deliberators.models import DecisionRecord

_DEFAULT_BASE_DIR = Path.home() / ".local" / "share" / "deliberators" / "decisions"


class DecisionStore:
    """Save and retrieve deliberation decisions as JSON files."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir or _DEFAULT_BASE_DIR

    def save(self, record: DecisionRecord) -> Path:
        """Write a DecisionRecord as JSON. Creates base_dir on first save."""
        self._base_dir.mkdir(parents=True, exist_ok=True)
        path = self._base_dir / f"{record.id}.json"
        path.write_text(json.dumps(self._to_dict(record), indent=2, ensure_ascii=False))
        return path

    def load(self, decision_id: str) -> DecisionRecord | None:
        """Load a DecisionRecord by full or prefix ID. Returns None if not found."""
        if not self._base_dir.exists():
            return None

        # Try exact match first
        exact = self._base_dir / f"{decision_id}.json"
        if exact.exists():
            return self._from_dict(json.loads(exact.read_text()))

        # Prefix match
        matches = list(self._base_dir.glob(f"{decision_id}*.json"))
        if len(matches) == 1:
            return self._from_dict(json.loads(matches[0].read_text()))

        return None

    def list_recent(self, limit: int = 20) -> list[DecisionRecord]:
        """List recent decisions, newest first."""
        if not self._base_dir.exists():
            return []

        files = sorted(self._base_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        records = []
        for f in files[:limit]:
            try:
                records.append(self._from_dict(json.loads(f.read_text())))
            except (json.JSONDecodeError, KeyError):
                continue
        return records

    @staticmethod
    def _to_dict(record: DecisionRecord) -> dict:
        """Serialize a DecisionRecord to a JSON-compatible dict."""
        return {
            "id": record.id,
            "timestamp": record.timestamp,
            "question": record.question,
            "preset_name": record.preset_name,
            "analysts": list(record.analysts),
            "editors": list(record.editors),
            "summary": record.summary,
            "key_positions": record.key_positions,
            "follow_up_of": record.follow_up_of,
        }

    @staticmethod
    def _from_dict(data: dict) -> DecisionRecord:
        """Deserialize a dict to a DecisionRecord."""
        return DecisionRecord(
            id=data["id"],
            timestamp=data["timestamp"],
            question=data["question"],
            preset_name=data["preset_name"],
            analysts=tuple(data["analysts"]),
            editors=tuple(data["editors"]),
            summary=data["summary"],
            key_positions=data["key_positions"],
            follow_up_of=data.get("follow_up_of"),
        )

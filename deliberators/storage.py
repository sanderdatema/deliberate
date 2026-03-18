"""Decision memory — structured JSON storage for deliberation results."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from deliberators.models import DecisionRecord, DeliberationResult

_DEFAULT_BASE_DIR = Path.home() / ".local" / "share" / "deliberators" / "decisions"


def _condense_positions(rounds: dict[int, dict[str, str]]) -> dict[str, str]:
    """Extract last-round output per analyst, truncated to ~200 chars."""
    if not rounds:
        return {}
    last_round = rounds[max(rounds.keys())]
    return {
        name: output[:200].rsplit(" ", 1)[0] + ("..." if len(output) > 200 else "")
        for name, output in last_round.items()
    }


def to_decision_record(
    result: DeliberationResult, follow_up_of: str | None = None,
) -> DecisionRecord:
    """Build a DecisionRecord from a DeliberationResult."""
    return DecisionRecord(
        id=uuid.uuid4().hex,
        timestamp=datetime.now(timezone.utc).isoformat(),
        question=result.question,
        preset_name=result.preset.name,
        analysts=tuple(result.rounds[1].keys()) if 1 in result.rounds else (),
        editors=tuple(result.editor_outputs.keys()),
        summary=result.samenvatter_output or "",
        key_positions=_condense_positions(result.rounds),
        follow_up_of=follow_up_of,
    )


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
        if not decision_id or not decision_id.strip():
            return None
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

"""Tests for decision memory storage."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from deliberators.models import DecisionRecord
from deliberators.storage import DecisionStore


def _make_record(
    record_id: str = "abc12345",
    question: str = "Should we refactor?",
    follow_up_of: str | None = None,
) -> DecisionRecord:
    return DecisionRecord(
        id=record_id,
        timestamp="2026-03-22T12:00:00Z",
        question=question,
        preset_name="balanced",
        analysts=("socrates", "occam", "holmes"),
        editors=("marx", "samenvatter"),
        summary="Just refactor it.",
        key_positions={"socrates": "Question everything", "occam": "Keep it simple"},
        follow_up_of=follow_up_of,
    )


class TestDecisionStore:
    def test_save_creates_json_file(self, tmp_path: Path) -> None:
        store = DecisionStore(base_dir=tmp_path)
        record = _make_record()
        path = store.save(record)
        assert path.exists()
        assert path.suffix == ".json"
        data = json.loads(path.read_text())
        assert data["id"] == "abc12345"
        assert data["question"] == "Should we refactor?"

    def test_load_by_full_id(self, tmp_path: Path) -> None:
        store = DecisionStore(base_dir=tmp_path)
        store.save(_make_record())
        loaded = store.load("abc12345")
        assert loaded is not None
        assert loaded.question == "Should we refactor?"

    def test_load_by_short_id_prefix(self, tmp_path: Path) -> None:
        store = DecisionStore(base_dir=tmp_path)
        store.save(_make_record())
        loaded = store.load("abc1")
        assert loaded is not None
        assert loaded.id == "abc12345"

    def test_load_nonexistent_returns_none(self, tmp_path: Path) -> None:
        store = DecisionStore(base_dir=tmp_path)
        assert store.load("nonexistent") is None

    def test_load_empty_id_returns_none(self, tmp_path: Path) -> None:
        store = DecisionStore(base_dir=tmp_path)
        store.save(_make_record())
        assert store.load("") is None

    def test_load_whitespace_id_returns_none(self, tmp_path: Path) -> None:
        store = DecisionStore(base_dir=tmp_path)
        store.save(_make_record())
        assert store.load("   ") is None

    def test_list_recent_ordered_newest_first(self, tmp_path: Path) -> None:
        store = DecisionStore(base_dir=tmp_path)
        store.save(_make_record("aaa", "First question"))
        time.sleep(0.05)  # Ensure different mtime
        store.save(_make_record("bbb", "Second question"))
        time.sleep(0.05)
        store.save(_make_record("ccc", "Third question"))

        records = store.list_recent()
        assert len(records) == 3
        assert records[0].id == "ccc"
        assert records[2].id == "aaa"

    def test_list_recent_respects_limit(self, tmp_path: Path) -> None:
        store = DecisionStore(base_dir=tmp_path)
        for i in range(5):
            store.save(_make_record(f"id{i}", f"Question {i}"))
        records = store.list_recent(limit=2)
        assert len(records) == 2

    def test_roundtrip_preserves_data(self, tmp_path: Path) -> None:
        store = DecisionStore(base_dir=tmp_path)
        original = _make_record(follow_up_of="parent123")
        store.save(original)
        loaded = store.load(original.id)
        assert loaded is not None
        assert loaded.id == original.id
        assert loaded.timestamp == original.timestamp
        assert loaded.question == original.question
        assert loaded.preset_name == original.preset_name
        assert loaded.analysts == original.analysts
        assert loaded.editors == original.editors
        assert loaded.summary == original.summary
        assert loaded.key_positions == original.key_positions
        assert loaded.follow_up_of == original.follow_up_of

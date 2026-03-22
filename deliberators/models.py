"""Data models for the deliberation engine."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


@dataclass(frozen=True)
class Persona:
    """A thinker persona loaded from YAML."""

    name: str
    model: str  # "opus" or "sonnet"
    domains: tuple[str, ...]
    role: Literal["analyst", "editor"]
    reasoning_style: str
    forbidden: tuple[str, ...]
    focus: str
    output_format: dict[str, bool]
    system_prompt: str


@dataclass(frozen=True)
class Preset:
    """A deliberation preset (quick/balanced/deep)."""

    name: str
    description: str
    max_rounds: int
    team_size: int = 5
    editor_count: int = 2
    analysts: tuple[str, ...] = ()
    editors: tuple[str, ...] = ()
    min_rounds: int = 1
    summarizer: str | None = None


@dataclass(frozen=True)
class Config:
    """Top-level configuration loaded from config.yaml."""

    default_preset: str
    rounds: int
    model: str
    presets: dict[str, Preset]
    timeout: int = 120
    max_concurrent: int = 10


@dataclass(frozen=True)
class ConvergenceResult:
    """Result of a convergence check after an analyst round."""

    should_continue: bool
    reason: str
    round_number: int


@dataclass(frozen=True)
class IntakeBrief:
    """Result of the intake phase — injected into analyst prompts."""

    question: str
    summary: str
    clarifications: tuple[tuple[str, str], ...]
    is_clear: bool


@dataclass(frozen=True)
class DecisionRecord:
    """A stored deliberation result for decision memory."""

    id: str
    timestamp: str
    question: str
    preset_name: str
    analysts: tuple[str, ...]
    editors: tuple[str, ...]
    summary: str
    key_positions: dict[str, str]
    follow_up_of: str | None = None


@dataclass(frozen=True)
class DeliberationEvent:
    """An event emitted during deliberation for streaming/UI."""

    type: Literal[
        "deliberation_started",
        "intake_started",
        "intake_completed",
        "team_selected",
        "agent_started",
        "agent_completed",
        "round_started",
        "round_completed",
        "convergence_started",
        "convergence_completed",
        "editorial_started",
        "editorial_completed",
        "deliberation_completed",
    ]
    agent_name: str | None = None
    round_number: int | None = None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeliberationResult:
    """Result of a complete deliberation run."""

    question: str
    preset: Preset
    rounds: dict[int, dict[str, str]] = field(default_factory=dict)
    editor_outputs: dict[str, str] = field(default_factory=dict)
    samenvatter_output: str | None = None
    code_context: str | None = None
    intake_brief: IntakeBrief | None = None
    synthesis_output: str | None = None


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

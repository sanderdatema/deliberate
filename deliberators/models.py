"""Data models for the deliberation engine."""

from __future__ import annotations

from dataclasses import dataclass, field
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

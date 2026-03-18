"""Data models for the deliberation engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class Persona:
    """A thinker persona loaded from YAML."""

    name: str
    role: Literal["analyst", "editor"]
    reasoning_style: str
    forbidden: list[str]
    focus: str
    output_format: dict[str, bool]
    system_prompt: str


@dataclass(frozen=True)
class Preset:
    """A deliberation preset (quick/balanced/deep)."""

    name: str
    description: str
    rounds: int
    analysts: list[str]
    editors: list[str]


@dataclass(frozen=True)
class Config:
    """Top-level configuration loaded from config.yaml."""

    default_preset: str
    rounds: int
    model: str
    presets: dict[str, Preset]


@dataclass(frozen=True)
class DeliberationEvent:
    """An event emitted during deliberation for streaming/UI."""

    type: Literal[
        "agent_started",
        "agent_completed",
        "round_started",
        "round_completed",
        "editorial_started",
        "editorial_completed",
        "deliberation_started",
        "deliberation_completed",
    ]
    agent_name: str | None = None
    round_number: int | None = None
    data: dict[str, Any] = field(default_factory=dict)

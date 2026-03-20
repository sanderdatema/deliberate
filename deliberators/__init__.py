"""Deliberators — Multi-perspectief AI deliberatie engine."""

from pathlib import Path

from deliberators.engine import DeliberationEngine, DeliberationResult
from deliberators.models import Config, DeliberationEvent, Persona, Preset


def get_data_path() -> Path:
    """Return the path to the bundled data directory."""
    return Path(__file__).parent / "data"


__all__ = [
    "Config",
    "DeliberationEngine",
    "DeliberationEvent",
    "DeliberationResult",
    "Persona",
    "Preset",
    "get_data_path",
]

"""Tests for deliberators.models dataclasses."""

import pytest

from deliberators.models import Config, DeliberationEvent, Persona, Preset


class TestPersona:
    def test_create_analyst(self):
        p = Persona(
            name="Test",
            model="opus",
            role="analyst",
            reasoning_style="Test style",
            forbidden=("a", "b"),
            focus="Test focus",
            output_format={"position": True, "confidence": True},
            system_prompt="You are FORBIDDEN from X. You MUST NOT Y.",
        )
        assert p.name == "Test"
        assert p.role == "analyst"
        assert len(p.forbidden) == 2

    def test_create_editor(self):
        p = Persona(
            name="Editor",
            model="sonnet",
            role="editor",
            reasoning_style="Editorial style",
            forbidden=("a", "b", "c"),
            focus="Find blind spots",
            output_format={"blind_spots": True, "synthesis": True},
            system_prompt="You are FORBIDDEN from X. You MUST NOT Y.",
        )
        assert p.role == "editor"

    def test_frozen(self):
        p = Persona(
            name="Test",
            model="opus",
            role="analyst",
            reasoning_style="",
            forbidden=("a", "b"),
            focus="",
            output_format={},
            system_prompt="FORBIDDEN MUST NOT",
        )
        with pytest.raises(AttributeError):
            p.name = "Changed"  # type: ignore[misc]


class TestPreset:
    def test_create(self):
        p = Preset(
            name="test",
            description="A test preset",
            rounds=2,
            analysts=("a", "b"),
            editors=("c",),
        )
        assert p.name == "test"
        assert p.rounds == 2
        assert len(p.analysts) == 2

    def test_frozen(self):
        p = Preset(name="t", description="", rounds=1, analysts=(), editors=())
        with pytest.raises(AttributeError):
            p.rounds = 3  # type: ignore[misc]


class TestConfig:
    def test_create(self):
        preset = Preset(name="q", description="", rounds=1, analysts=("a",), editors=("b",))
        c = Config(
            default_preset="q",
            rounds=2,
            model="opus",
            presets={"q": preset},
        )
        assert c.default_preset == "q"
        assert "q" in c.presets


class TestDeliberationEvent:
    @pytest.mark.parametrize(
        "event_type",
        [
            "agent_started",
            "agent_completed",
            "round_started",
            "round_completed",
            "editorial_started",
            "editorial_completed",
            "deliberation_started",
            "deliberation_completed",
        ],
    )
    def test_event_types(self, event_type: str):
        e = DeliberationEvent(type=event_type)
        assert e.type == event_type
        assert e.agent_name is None
        assert e.round_number is None
        assert e.data == {}

    def test_event_with_data(self):
        e = DeliberationEvent(
            type="agent_completed",
            agent_name="socrates",
            round_number=1,
            data={"output": "Some analysis", "confidence": 0.85},
        )
        assert e.agent_name == "socrates"
        assert e.round_number == 1
        assert e.data["confidence"] == 0.85

"""Tests for deliberators.models dataclasses."""

import pytest

from deliberators.models import Config, ConvergenceResult, DeliberationEvent, IntakeBrief, Persona, Preset


class TestPersona:
    def test_create_analyst(self):
        p = Persona(
            name="Test",
            model="opus",
            domains=("testing", "quality"),
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
            domains=("synthesis",),
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
            domains=("testing",),
            role="analyst",
            reasoning_style="",
            forbidden=("a", "b"),
            focus="",
            output_format={},
            system_prompt="FORBIDDEN MUST NOT",
        )
        with pytest.raises(AttributeError):
            p.name = "Changed"  # type: ignore[misc]

    def test_domains_field(self):
        p = Persona(
            name="Test",
            model="opus",
            domains=("security", "cryptography", "threat_modeling"),
            role="analyst",
            reasoning_style="Test",
            forbidden=("a", "b"),
            focus="Test",
            output_format={},
            system_prompt="FORBIDDEN MUST NOT",
        )
        assert p.domains == ("security", "cryptography", "threat_modeling")
        assert isinstance(p.domains, tuple)
        assert len(p.domains) == 3


class TestPreset:
    def test_create(self):
        p = Preset(
            name="test",
            description="A test preset",
            max_rounds=2,
            analysts=("a", "b"),
            editors=("c",),
        )
        assert p.name == "test"
        assert p.max_rounds == 2
        assert p.min_rounds == 1  # default
        assert len(p.analysts) == 2

    def test_create_with_min_rounds(self):
        p = Preset(
            name="test",
            description="",
            max_rounds=3,
            analysts=("a",),
            editors=("b",),
            min_rounds=2,
        )
        assert p.min_rounds == 2
        assert p.max_rounds == 3

    def test_frozen(self):
        p = Preset(name="t", description="", max_rounds=1, analysts=(), editors=())
        with pytest.raises(AttributeError):
            p.max_rounds = 3  # type: ignore[misc]


class TestConvergenceResult:
    def test_create(self):
        r = ConvergenceResult(should_continue=True, reason="Positions diverging", round_number=1)
        assert r.should_continue is True
        assert r.reason == "Positions diverging"
        assert r.round_number == 1

    def test_frozen(self):
        r = ConvergenceResult(should_continue=False, reason="Converged", round_number=2)
        with pytest.raises(AttributeError):
            r.should_continue = True  # type: ignore[misc]

    def test_stop(self):
        r = ConvergenceResult(should_continue=False, reason="All agreed", round_number=1)
        assert r.should_continue is False


class TestConfig:
    def test_create(self):
        preset = Preset(name="q", description="", max_rounds=1, analysts=("a",), editors=("b",))
        c = Config(
            default_preset="q",
            model="opus",
            presets={"q": preset},
        )
        assert c.default_preset == "q"
        assert "q" in c.presets


class TestDeliberationEvent:
    @pytest.mark.parametrize(
        "event_type",
        [
            "deliberation_started",
            "intake_started",
            "intake_completed",
            "agent_started",
            "agent_completed",
            "round_started",
            "round_completed",
            "convergence_started",
            "convergence_completed",
            "editorial_started",
            "editorial_completed",
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


class TestIntakeBrief:
    def test_create(self):
        brief = IntakeBrief(
            question="test question",
            summary="This is about X",
            clarifications=(("Q?", "A"),),
            is_clear=True,
        )
        assert brief.question == "test question"
        assert brief.is_clear is True
        assert len(brief.clarifications) == 1

    def test_frozen(self):
        brief = IntakeBrief(question="q", summary="s", clarifications=(), is_clear=True)
        with pytest.raises(AttributeError):
            brief.summary = "changed"  # type: ignore[misc]

    def test_empty_clarifications(self):
        brief = IntakeBrief(question="q", summary="s", clarifications=(), is_clear=True)
        assert brief.clarifications == ()

    def test_intake_event_types(self):
        e1 = DeliberationEvent(type="intake_started")
        assert e1.type == "intake_started"
        e2 = DeliberationEvent(type="intake_completed", data={"is_clear": True})
        assert e2.data["is_clear"] is True

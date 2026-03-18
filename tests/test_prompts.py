"""Tests for deliberators.prompts — pure prompt-building functions."""

from __future__ import annotations

from deliberators.models import DecisionRecord, IntakeBrief, Persona
from deliberators.prompts import (
    build_analyst_prompt,
    build_editor_prompt,
    build_persona_catalog,
    compile_analyst_output,
)


def _persona(name: str = "test", role: str = "analyst") -> Persona:
    return Persona(
        name=name, model="sonnet", domains=("ethics", "logic"), role=role,
        reasoning_style="dialectical", forbidden=("dogma", "bias"),
        focus="truth", output_format={},
        system_prompt="You are FORBIDDEN from dogma. You MUST NOT assume.",
    )


class TestBuildPersonaCatalog:
    def test_includes_all_personas(self) -> None:
        personas = {"alice": _persona("Alice"), "bob": _persona("Bob", "editor")}
        catalog = build_persona_catalog(personas)
        assert "alice" in catalog
        assert "bob" in catalog
        assert "role=analyst" in catalog
        assert "role=editor" in catalog

    def test_sorted_by_key(self) -> None:
        personas = {"zeta": _persona("Zeta"), "alpha": _persona("Alpha")}
        catalog = build_persona_catalog(personas)
        lines = catalog.strip().splitlines()
        assert "alpha" in lines[0]
        assert "zeta" in lines[1]

    def test_includes_domains(self) -> None:
        catalog = build_persona_catalog({"p": _persona()})
        assert "ethics" in catalog
        assert "logic" in catalog


class TestBuildAnalystPrompt:
    def test_basic_round_1(self) -> None:
        prompt = build_analyst_prompt(_persona(), "What is justice?", 1, None)
        assert "QUESTION FOR DELIBERATION" in prompt
        assert "What is justice?" in prompt

    def test_round_2_includes_prior_output(self) -> None:
        prior = {"socrates": "Justice is harmony"}
        prompt = build_analyst_prompt(_persona(), "What is justice?", 2, prior)
        assert "ROUND 1 PERSPECTIVES" in prompt
        assert "Justice is harmony" in prompt
        assert "THIS IS ROUND 2" in prompt

    def test_includes_code_context(self) -> None:
        prompt = build_analyst_prompt(
            _persona(), "Review this", 1, None, code_context="def foo(): pass"
        )
        assert "CODE UNDER REVIEW" in prompt
        assert "def foo(): pass" in prompt

    def test_includes_intake_brief(self) -> None:
        brief = IntakeBrief(
            question="Q", summary="About ethics", clarifications=(), is_clear=True
        )
        prompt = build_analyst_prompt(_persona(), "Q", 1, None, intake_brief=brief)
        assert "INTAKE CONTEXT" in prompt
        assert "About ethics" in prompt

    def test_includes_prior_decision(self) -> None:
        prior = DecisionRecord(
            id="abc", timestamp="2026-01-01", question="Old Q",
            preset_name="balanced", analysts=(), editors=(),
            summary="Old conclusion", key_positions={"s": "pos"},
        )
        prompt = build_analyst_prompt(_persona(), "New Q", 1, None, prior_decision=prior)
        assert "PRIOR DELIBERATION CONTEXT" in prompt
        assert "Old conclusion" in prompt


class TestBuildEditorPrompt:
    def test_basic_editor_prompt(self) -> None:
        prompt = build_editor_prompt(
            _persona("editor", "editor"), "What is justice?",
            "## Round 1\n### socrates\nAnalysis", {},
        )
        assert "ORIGINAL QUESTION" in prompt
        assert "ANALYST PERSPECTIVES" in prompt

    def test_includes_code_context(self) -> None:
        prompt = build_editor_prompt(
            _persona("editor", "editor"), "Review", "analyst output", {},
            code_context="def bar(): pass",
        )
        assert "CODE UNDER REVIEW" in prompt

    def test_includes_prior_editor_output(self) -> None:
        prompt = build_editor_prompt(
            _persona("editor", "editor"), "Q", "analyst output",
            {"marx": "First editorial"},
        )
        assert "PRIOR EDITORIAL ANALYSIS" in prompt
        assert "First editorial" in prompt


class TestCompileAnalystOutput:
    def test_single_round(self) -> None:
        rounds = {1: {"socrates": "Analysis A", "occam": "Analysis B"}}
        output = compile_analyst_output(rounds)
        assert "## Round 1" in output
        assert "### socrates" in output
        assert "### occam" in output

    def test_multiple_rounds_ordered(self) -> None:
        rounds = {
            2: {"socrates": "Round 2"},
            1: {"socrates": "Round 1"},
        }
        output = compile_analyst_output(rounds)
        assert output.index("## Round 1") < output.index("## Round 2")

    def test_empty_rounds(self) -> None:
        assert compile_analyst_output({}) == ""

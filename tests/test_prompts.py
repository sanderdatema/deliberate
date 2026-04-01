"""Tests for deliberators.prompts — pure prompt-building functions."""

from __future__ import annotations

from deliberators.models import DecisionRecord, IntakeBrief, Persona
from deliberators.models import Preset
from deliberators.prompts import (
    build_analyst_prompt,
    build_convergence_prompt,
    build_editor_prompt,
    build_persona_catalog,
    build_synthesis_prompt,
    build_team_selection_prompt,
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


class TestBuildTeamSelectionPrompt:
    def _preset(self, team_size: int = 3, editor_count: int = 1) -> Preset:
        return Preset(
            name="quick", description="", max_rounds=1,
            team_size=team_size, editor_count=editor_count,
        )

    def test_includes_question(self) -> None:
        prompt = build_team_selection_prompt({}, "What is justice?", self._preset())
        assert "What is justice?" in prompt

    def test_includes_team_size(self) -> None:
        prompt = build_team_selection_prompt({}, "Q", self._preset(team_size=4, editor_count=2))
        assert "4 analysts" in prompt
        assert "2 editors" in prompt

    def test_includes_catalog(self) -> None:
        personas = {"alice": _persona("Alice")}
        prompt = build_team_selection_prompt(personas, "Q", self._preset())
        assert "alice" in prompt

    def test_includes_intake_brief(self) -> None:
        brief = IntakeBrief(question="Q", summary="About justice", clarifications=(), is_clear=True)
        prompt = build_team_selection_prompt({}, "Q", self._preset(), intake_brief=brief)
        assert "QUESTION CONTEXT" in prompt
        assert "About justice" in prompt

    def test_skips_intake_brief_when_no_summary(self) -> None:
        brief = IntakeBrief(question="Q", summary="", clarifications=(), is_clear=True)
        prompt = build_team_selection_prompt({}, "Q", self._preset(), intake_brief=brief)
        assert "QUESTION CONTEXT" not in prompt

    def test_includes_code_review_note_when_code_context(self) -> None:
        prompt = build_team_selection_prompt({}, "Q", self._preset(), code_context="def foo(): pass")
        assert "code review" in prompt.lower()

    def test_no_code_review_note_without_code_context(self) -> None:
        prompt = build_team_selection_prompt({}, "Q", self._preset())
        assert "code review" not in prompt.lower()


class TestBuildConvergencePrompt:
    def test_includes_round_output(self) -> None:
        prompt = build_convergence_prompt(1, {"socrates": "Justice is harmony"})
        assert "Justice is harmony" in prompt
        assert "### socrates" in prompt

    def test_includes_round_number(self) -> None:
        prompt = build_convergence_prompt(2, {"socrates": "Output"})
        assert "ROUND 2" in prompt
        assert "Round 3" in prompt

    def test_includes_intake_brief(self) -> None:
        brief = IntakeBrief(question="Q", summary="Context summary", clarifications=(), is_clear=True)
        prompt = build_convergence_prompt(1, {}, intake_brief=brief)
        assert "QUESTION CONTEXT" in prompt
        assert "Context summary" in prompt

    def test_skips_intake_when_no_summary(self) -> None:
        brief = IntakeBrief(question="Q", summary="", clarifications=(), is_clear=True)
        prompt = build_convergence_prompt(1, {}, intake_brief=brief)
        assert "QUESTION CONTEXT" not in prompt


class TestBuildSynthesisPrompt:
    def test_includes_question(self) -> None:
        prompt = build_synthesis_prompt("What is justice?", "analyst output", {}, None, 1)
        assert "What is justice?" in prompt

    def test_includes_analyst_output(self) -> None:
        prompt = build_synthesis_prompt("Q", "Analyst perspective here", {}, None, 1)
        assert "Analyst perspective here" in prompt

    def test_includes_num_rounds(self) -> None:
        prompt = build_synthesis_prompt("Q", "", {}, None, 3)
        assert "3" in prompt

    def test_includes_editor_output(self) -> None:
        prompt = build_synthesis_prompt("Q", "", {"marx": "Editorial view"}, None, 1)
        assert "EDITORIAL ANALYSIS" in prompt
        assert "Editorial view" in prompt

    def test_skips_editorial_when_empty(self) -> None:
        prompt = build_synthesis_prompt("Q", "", {}, None, 1)
        assert "EDITORIAL ANALYSIS" not in prompt

    def test_includes_samenvatter(self) -> None:
        prompt = build_synthesis_prompt("Q", "", {}, "Summary conclusion", 1)
        assert "SAMENVATTER" in prompt
        assert "Summary conclusion" in prompt

    def test_skips_samenvatter_when_none(self) -> None:
        prompt = build_synthesis_prompt("Q", "", {}, None, 1)
        assert "SAMENVATTER" not in prompt


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

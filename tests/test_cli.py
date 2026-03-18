"""Tests for CLI entry point and formatter."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from deliberators.__main__ import build_parser
from deliberators.engine import DeliberationResult
from deliberators.formatter import ResultFormatter
from deliberators.loader import PersonaLoader
from deliberators.models import Persona, Preset

PERSONAS_DIR = Path("personas")


class TestCLIHelp:
    def test_help_exits_zero(self) -> None:
        """--help should exit 0 and show usage."""
        result = subprocess.run(
            [sys.executable, "-m", "deliberators", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "deliberators" in result.stdout
        assert "question" in result.stdout

    def test_missing_question_exits_nonzero(self) -> None:
        """Missing required 'question' arg should exit non-zero."""
        result = subprocess.run(
            [sys.executable, "-m", "deliberators"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0


class TestResultFormatter:
    @pytest.fixture()
    def personas(self) -> dict[str, Persona]:
        return PersonaLoader.load_all(PERSONAS_DIR)

    def _make_result(self) -> DeliberationResult:
        return DeliberationResult(
            question="Should we refactor the auth module?",
            preset=Preset(
                name="quick",
                description="Quick analysis",
                rounds=1,
                analysts=["occam", "holmes", "lupin"],
                editors=["marx", "samenvatter"],
            ),
            rounds={
                1: {
                    "occam": "Occam's analysis: simplify everything",
                    "holmes": "Holmes's analysis: observe the evidence",
                    "lupin": "Lupin's analysis: invert the question",
                },
            },
            editor_outputs={
                "marx": "Marx editorial: collective blind spots",
            },
            samenvatter_output="Kort: just refactor the auth module, it's simpler than you think.",
        )

    def test_format_contains_question(self, personas: dict[str, Persona]) -> None:
        formatter = ResultFormatter(personas)
        result = self._make_result()
        output = formatter.format(result)
        assert "Should we refactor the auth module?" in output

    def test_format_contains_round_headers(self, personas: dict[str, Persona]) -> None:
        formatter = ResultFormatter(personas)
        result = self._make_result()
        output = formatter.format(result)
        assert "## Ronde 1" in output

    def test_format_contains_analyst_output(self, personas: dict[str, Persona]) -> None:
        formatter = ResultFormatter(personas)
        result = self._make_result()
        output = formatter.format(result)
        assert "Occam's analysis" in output
        assert "Holmes's analysis" in output
        assert "Lupin's analysis" in output

    def test_format_contains_editor_output(self, personas: dict[str, Persona]) -> None:
        formatter = ResultFormatter(personas)
        result = self._make_result()
        output = formatter.format(result)
        assert "Marx editorial" in output

    def test_format_contains_samenvatter(self, personas: dict[str, Persona]) -> None:
        formatter = ResultFormatter(personas)
        result = self._make_result()
        output = formatter.format(result)
        assert "Kort & Concreet" in output
        assert "just refactor the auth module" in output

    def test_format_samenvatter_before_full_report(self, personas: dict[str, Persona]) -> None:
        """Samenvatter (Kort & Concreet) appears before the full report."""
        formatter = ResultFormatter(personas)
        result = self._make_result()
        output = formatter.format(result)
        kort_pos = output.index("Kort & Concreet")
        deliberatie_pos = output.index("# Deliberatie:")
        assert kort_pos < deliberatie_pos

    def test_format_is_valid_markdown(self, personas: dict[str, Persona]) -> None:
        """Output should contain markdown headers."""
        formatter = ResultFormatter(personas)
        result = self._make_result()
        output = formatter.format(result)
        assert output.count("# ") >= 2  # At least title + round header
        assert output.count("## ") >= 2
        assert output.count("### ") >= 3  # At least 3 analysts


class TestCLIParser:
    """Tests for the CLI argument parser."""

    def test_accepts_files_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["question", "--files", "a.py", "b.py"])
        assert args.files == [Path("a.py"), Path("b.py")]

    def test_files_default_is_none(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["question"])
        assert args.files is None

    def test_accepts_code_presets(self) -> None:
        parser = build_parser()
        for preset in ["code_quick", "code_balanced", "code_deep"]:
            args = parser.parse_args(["question", "--preset", preset])
            assert args.preset == preset

    def test_accepts_general_presets(self) -> None:
        parser = build_parser()
        for preset in ["quick", "balanced", "deep"]:
            args = parser.parse_args(["question", "--preset", preset])
            assert args.preset == preset

    def test_files_with_preset(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "review this", "--preset", "code_balanced", "--files", "main.py",
        ])
        assert args.preset == "code_balanced"
        assert args.files == [Path("main.py")]
        assert args.question == "review this"

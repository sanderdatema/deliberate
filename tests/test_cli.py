"""Tests for CLI entry point and formatter."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from deliberators.__main__ import build_parser
from deliberators.web_pusher import WebPusher
from deliberators.engine import DeliberationResult
from deliberators.formatter import ResultFormatter
from deliberators.loader import PersonaLoader
from deliberators.models import DeliberationEvent, Persona, Preset

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

    _SYNTHESIS = (
        "## Het Landschap\nThe question is about technical debt.\n\n"
        "## Spanningsvelden\nSpeed vs quality is the core tension.\n\n"
        "## Blinde Vlekken\nNobody questioned whether the module is actually used.\n\n"
        "## Actiepunten\n1. Audit usage\n2. Plan migration\n3. Set deadline"
    )

    def _make_result(self, with_synthesis: bool = True) -> DeliberationResult:
        return DeliberationResult(
            question="Should we refactor the auth module?",
            preset=Preset(
                name="quick",
                description="Quick analysis",
                max_rounds=1,
                analysts=("occam", "holmes", "lupin"),
                editors=("marx", "samenvatter"),
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
            synthesis_output=self._SYNTHESIS if with_synthesis else None,
        )

    def test_format_contains_question(self, personas: dict[str, Persona]) -> None:
        formatter = ResultFormatter(personas)
        result = self._make_result()
        output = formatter.format(result)
        assert "Should we refactor the auth module?" in output

    def test_format_contains_thematic_sections(self, personas: dict[str, Persona]) -> None:
        """Thematic report contains synthesis sections."""
        formatter = ResultFormatter(personas)
        result = self._make_result()
        output = formatter.format(result)
        assert "## Het Landschap" in output
        assert "## Spanningsvelden" in output
        assert "## Blinde Vlekken" in output
        assert "## Actiepunten" in output

    def test_format_contains_appendix_with_personas(self, personas: dict[str, Persona]) -> None:
        """Thematic report has Volledig Verslag appendix with per-persona output."""
        formatter = ResultFormatter(personas)
        result = self._make_result()
        output = formatter.format(result)
        assert "## Volledig Verslag" in output
        assert "Occam's analysis" in output
        assert "Holmes's analysis" in output
        assert "Lupin's analysis" in output
        assert "Marx editorial" in output

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

    def test_format_fallback_without_synthesis(self, personas: dict[str, Persona]) -> None:
        """Without synthesis, falls back to per-persona format (no Volledig Verslag)."""
        formatter = ResultFormatter(personas)
        result = self._make_result(with_synthesis=False)
        output = formatter.format(result)
        assert "Volledig Verslag" not in output
        assert "Het Landschap" not in output
        # But still contains per-persona output directly
        assert "Occam's analysis" in output
        assert "Ronde 1" in output

    def test_format_is_valid_markdown(self, personas: dict[str, Persona]) -> None:
        """Output should contain markdown headers."""
        formatter = ResultFormatter(personas)
        result = self._make_result()
        output = formatter.format(result)
        assert output.count("# ") >= 2  # At least title + thematic headers
        assert output.count("## ") >= 4  # Kort & Concreet + thematic sections + appendix


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

    def test_accepts_presets(self) -> None:
        parser = build_parser()
        for preset in ["quick", "balanced", "deep"]:
            args = parser.parse_args(["question", "--preset", preset])
            assert args.preset == preset

    def test_files_with_preset(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "review this", "--preset", "balanced", "--files", "main.py",
        ])
        assert args.preset == "balanced"
        assert args.files == [Path("main.py")]
        assert args.question == "review this"


class TestWebPusherClientReuse:
    """AC-1: WebPusher reuses a single httpx.AsyncClient."""

    def test_single_client_instance(self) -> None:
        """WebPusher creates one client in __init__, not per call."""
        pusher = WebPusher("http://localhost:8000")
        assert isinstance(pusher._client, httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_reuses_client_across_calls(self) -> None:
        """All push methods use the same client instance."""
        pusher = WebPusher("http://localhost:8000")
        pusher.session_id = "test-session"

        # Track which client instance is used
        original_client = pusher._client
        post_calls: list[httpx.AsyncClient] = []

        original_post = original_client.post

        async def tracking_post(*args, **kwargs):
            post_calls.append(pusher._client)
            # Return a mock response
            mock_resp = httpx.Response(200, json={"ok": True})
            return mock_resp

        with patch.object(original_client, "post", side_effect=tracking_post):
            event = DeliberationEvent(type="round_started", round_number=1)
            await pusher.push_event(event)
            await pusher.push_text("test-agent", "hello")

        # All calls should have used the same client
        assert len(post_calls) == 2
        assert all(c is original_client for c in post_calls)

    @pytest.mark.asyncio
    async def test_close_closes_client(self) -> None:
        """close() calls aclose() on the underlying client."""
        pusher = WebPusher("http://localhost:8000")
        with patch.object(pusher._client, "aclose", new_callable=AsyncMock) as mock_aclose:
            await pusher.close()
            mock_aclose.assert_called_once()

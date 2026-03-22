"""Quality and integration tests — verify behavioral correctness beyond format.

These address the self-evaluation finding: "159 format tests, zero quality tests."
They verify prompt construction, pipeline wiring, and output structure.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from deliberators.engine import DeliberationEngine
from deliberators.loader import ConfigLoader, PersonaLoader
from deliberators.models import Config, DeliberationEvent, Persona

# Reuse mock helpers and test config from test_engine
from tests.test_engine import make_mock_subprocess, _make_test_config

PERSONAS_DIR = Path("personas")


@pytest.fixture()
def config() -> Config:
    return _make_test_config()


@pytest.fixture()
def personas() -> dict[str, Persona]:
    return PersonaLoader.load_all(PERSONAS_DIR)


class TestPromptConstruction:
    """AC-4: Verify prompts are correctly constructed."""

    @pytest.mark.asyncio
    async def test_system_prompt_passed_as_cli_flag(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """Persona system_prompt goes in --system-prompt flag, not in stdin."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "quick")

        for call in tracker.calls[1:]:  # skip intake agent (index 0)
            system = call["system_prompt"]
            assert "FORBIDDEN" in system or "MUST NOT" in system, (
                f"--system-prompt should contain persona constraints, got: {system[:100]}"
            )
            # Stdin (user prompt) should NOT contain the system prompt's output format
            stdin_text = call["process"].stdin_text
            assert "FORMAT YOUR RESPONSE" not in stdin_text, (
                "system_prompt content leaked into stdin prompt"
            )

    @pytest.mark.asyncio
    async def test_round2_prompts_contain_round2_marker(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """Round 2 prompts must contain 'THIS IS ROUND 2'."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "balanced")

        # Round 2 calls are 8-12 (after 1 intake + 5 Round 1 + 1 convergence)
        round2_calls = tracker.calls[7:12]
        for call in round2_calls:
            content = call["process"].stdin_text
            assert "THIS IS ROUND 2" in content

    @pytest.mark.asyncio
    async def test_round2_prompts_contain_full_round1_output(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """Round 2 must include complete Round 1 output, not summaries."""
        tracker = make_mock_subprocess(default="Detailed analysis with evidence and reasoning")
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "balanced")

        round2_calls = tracker.calls[7:12]
        for call in round2_calls:
            content = call["process"].stdin_text
            assert "Detailed analysis with evidence and reasoning" in content

    @pytest.mark.asyncio
    async def test_editor_prompts_contain_all_rounds(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """Editor prompts include analyst output from ALL rounds."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "balanced")

        # Editor calls are after 1 intake + 5 R1 + 1 convergence + 5 R2 = 12
        editor_calls = tracker.calls[12:]
        for call in editor_calls:
            content = call["process"].stdin_text
            assert "Round 1" in content
            assert "Round 2" in content

    @pytest.mark.asyncio
    async def test_samenvatter_prompt_contains_editor_output(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """Samenvatter sees all prior editor output."""
        response_map = {
            "Karl Marx": "Marx: shared blind spots identified",
            "Georg Hegel": "Hegel: dialectical synthesis found",
            "Hannah Arendt": "Arendt: mechanisms exposed",
        }
        tracker = make_mock_subprocess(response_map=response_map)
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "balanced")

        samenvatter_call = tracker.calls[-1]
        content = samenvatter_call["process"].stdin_text
        assert "Marx: shared blind spots identified" in content
        assert "Hegel: dialectical synthesis found" in content
        assert "Arendt: mechanisms exposed" in content


class TestPipelineWiring:
    """AC-5: Verify all components are correctly wired together."""

    @pytest.mark.asyncio
    async def test_all_preset_analysts_in_result(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """Every analyst listed in the preset produces output."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            preset = ConfigLoader.get_preset(config, "balanced")
            result = await engine.run("Test question", "balanced")

        for analyst in preset.analysts:
            assert analyst in result.rounds[1], f"Missing analyst {analyst} in round 1"
            assert analyst in result.rounds[2], f"Missing analyst {analyst} in round 2"

    @pytest.mark.asyncio
    async def test_all_preset_editors_in_result(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """Every editor (except samenvatter) appears in editor_outputs."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            preset = ConfigLoader.get_preset(config, "balanced")
            result = await engine.run("Test question", "balanced")

        for editor in preset.editors:
            if editor == "samenvatter":
                assert result.samenvatter_output is not None
            else:
                assert editor in result.editor_outputs, f"Missing editor {editor}"

    @pytest.mark.asyncio
    async def test_event_sequence_structure(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """Event sequence follows correct structural pattern."""
        events: list[DeliberationEvent] = []
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(
                config, personas, on_event=lambda e: events.append(e)
            )
            await engine.run("Test question", "balanced")

        types = [e.type for e in events]

        # Must start and end correctly
        assert types[0] == "deliberation_started"
        assert types[-1] == "deliberation_completed"

        # Must have exactly 2 round_started/completed pairs
        assert types.count("round_started") == 2
        assert types.count("round_completed") == 2

        # Must have editorial section
        assert "editorial_started" in types
        assert "editorial_completed" in types

        # Every agent_started must have a matching agent_completed
        started = [e.agent_name for e in events if e.type == "agent_started"]
        completed = [e.agent_name for e in events if e.type == "agent_completed"]
        assert sorted(started) == sorted(completed)

    @pytest.mark.asyncio
    async def test_no_empty_outputs(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """No analyst or editor output should be empty."""
        tracker = make_mock_subprocess(default="Substantive output")
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            result = await engine.run("Test question", "balanced")

        for round_num, round_data in result.rounds.items():
            for name, output in round_data.items():
                assert len(output) > 0, f"Empty output for {name} in round {round_num}"

        for name, output in result.editor_outputs.items():
            assert len(output) > 0, f"Empty output for editor {name}"

        assert result.samenvatter_output and len(result.samenvatter_output) > 0

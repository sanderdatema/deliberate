"""Tests for deliberators.engine — orchestration with mocked Anthropic API."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deliberators.engine import DeliberationEngine, DeliberationResult
from deliberators.loader import ConfigLoader, PersonaLoader
from deliberators.models import Config, DeliberationEvent, Persona, Preset

PERSONAS_DIR = Path("personas")
CONFIG_PATH = Path("config.yaml")


class MockStream:
    """Mock for client.messages.stream() async context manager."""

    def __init__(self, text: str = "Mock response") -> None:
        self._text = text
        self._chunks = [text[i : i + 10] for i in range(0, len(text), 10)] or [text]

    async def __aenter__(self) -> MockStream:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    @property
    def text_stream(self) -> MockTextStream:
        return MockTextStream(self._chunks)


class MockTextStream:
    """Async iterator over text chunks."""

    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks
        self._index = 0

    def __aiter__(self) -> MockTextStream:
        return self

    async def __anext__(self) -> str:
        if self._index >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self._index]
        self._index += 1
        return chunk


def make_mock_client(response_map: dict[str, str] | None = None, default: str = "Mock output") -> AsyncMock:
    """Create a mock AsyncAnthropic client.

    response_map: maps persona name (from system prompt) to response text.
    """
    client = AsyncMock()
    call_count = 0

    def stream_side_effect(**kwargs):  # noqa: ANN003
        nonlocal call_count
        call_count += 1
        system = kwargs.get("system", "")
        if response_map:
            for name, response in response_map.items():
                if name.lower() in system.lower():
                    return MockStream(response)
        return MockStream(f"{default} #{call_count}")

    client.messages.stream = MagicMock(side_effect=stream_side_effect)
    return client


@pytest.fixture()
def config() -> Config:
    return ConfigLoader.load(CONFIG_PATH)


@pytest.fixture()
def personas() -> dict[str, Persona]:
    return PersonaLoader.load_all(PERSONAS_DIR)


class TestQuickPreset:
    """Quick preset: 3 analysts, 1 round, 2 editors (marx + samenvatter)."""

    @pytest.mark.asyncio
    async def test_correct_agent_count(self, config: Config, personas: dict[str, Persona]) -> None:
        """AC-1: quick = 3 analyst calls + 2 editor calls = 5 total."""
        client = make_mock_client()
        engine = DeliberationEngine(client, config, personas)

        result = await engine.run("Test question", "quick")

        assert client.messages.stream.call_count == 5  # 3 analysts + 2 editors

    @pytest.mark.asyncio
    async def test_result_structure(self, config: Config, personas: dict[str, Persona]) -> None:
        """AC-1: Result has correct fields."""
        client = make_mock_client()
        engine = DeliberationEngine(client, config, personas)

        result = await engine.run("Test question", "quick")

        assert result.question == "Test question"
        assert result.preset.name == "quick"
        assert 1 in result.rounds
        assert len(result.rounds[1]) == 3  # 3 analysts
        assert "marx" in result.editor_outputs
        assert result.samenvatter_output is not None

    @pytest.mark.asyncio
    async def test_only_one_round(self, config: Config, personas: dict[str, Persona]) -> None:
        """Quick preset has rounds=1, so only Round 1 exists."""
        client = make_mock_client()
        engine = DeliberationEngine(client, config, personas)

        result = await engine.run("Test question", "quick")

        assert len(result.rounds) == 1
        assert 2 not in result.rounds


class TestBalancedPreset:
    """Balanced preset: 5 analysts, 2 rounds, 4 editors."""

    @pytest.mark.asyncio
    async def test_correct_agent_count(self, config: Config, personas: dict[str, Persona]) -> None:
        """AC-1: balanced = 5 analysts × 2 rounds + 4 editors = 14 total."""
        client = make_mock_client()
        engine = DeliberationEngine(client, config, personas)

        result = await engine.run("Test question", "balanced")

        assert client.messages.stream.call_count == 14

    @pytest.mark.asyncio
    async def test_two_rounds(self, config: Config, personas: dict[str, Persona]) -> None:
        """Balanced has 2 analyst rounds."""
        client = make_mock_client()
        engine = DeliberationEngine(client, config, personas)

        result = await engine.run("Test question", "balanced")

        assert 1 in result.rounds
        assert 2 in result.rounds
        assert len(result.rounds[1]) == 5
        assert len(result.rounds[2]) == 5


class TestParallelAndSequential:
    """AC-2: Analysts parallel, editors sequential."""

    @pytest.mark.asyncio
    async def test_analysts_run_via_gather(self, config: Config, personas: dict[str, Persona]) -> None:
        """Verify analyst round uses asyncio.gather (parallel execution)."""
        client = make_mock_client()
        engine = DeliberationEngine(client, config, personas)

        # Patch asyncio.gather to verify it's called
        original_gather = asyncio.gather
        gather_calls: list[int] = []

        async def tracking_gather(*coros, **kwargs):  # noqa: ANN003, ANN002
            gather_calls.append(len(coros))
            return await original_gather(*coros, **kwargs)

        with patch("deliberators.engine.asyncio.gather", side_effect=tracking_gather):
            await engine.run("Test question", "quick")

        # Should have been called once for 1 round with 3 analysts
        assert len(gather_calls) == 1
        assert gather_calls[0] == 3

    @pytest.mark.asyncio
    async def test_editors_receive_prior_editor_output(self, config: Config, personas: dict[str, Persona]) -> None:
        """AC-2: Each editor sees prior editors' output."""
        response_map = {
            "Karl Marx": "Marx editorial output",
            "Georg Hegel": "Hegel editorial output",
            "Hannah Arendt": "Arendt editorial output",
        }
        client = make_mock_client(response_map=response_map)
        engine = DeliberationEngine(client, config, personas)

        await engine.run("Test question", "balanced")

        # Check Hegel's call included Marx's output
        calls = client.messages.stream.call_args_list
        # Find the Hegel call (system prompt contains "Georg Hegel")
        hegel_calls = [c for c in calls if "Georg Hegel" in (c.kwargs.get("system", "") or "")]
        assert len(hegel_calls) == 1
        hegel_prompt = hegel_calls[0].kwargs["messages"][0]["content"]
        assert "Marx editorial output" in hegel_prompt

        # Find the Arendt call
        arendt_calls = [c for c in calls if "Hannah Arendt" in (c.kwargs.get("system", "") or "")]
        assert len(arendt_calls) == 1
        arendt_prompt = arendt_calls[0].kwargs["messages"][0]["content"]
        assert "Marx editorial output" in arendt_prompt
        assert "Hegel editorial output" in arendt_prompt


class TestRound2FullOutput:
    """AC-3: Round 2 receives full Round 1 output, not a summary."""

    @pytest.mark.asyncio
    async def test_round2_contains_full_round1(self, config: Config, personas: dict[str, Persona]) -> None:
        """Round 2 prompt includes complete Round 1 text."""
        response_map = {
            "Socrates": "Socrates full analysis with detailed challenges and questions",
            "Willem van Occam": "Occam thorough razor analysis with evidence chains",
            "Leonardo da Vinci": "Da Vinci cross-domain patterns with structural analogies",
            "Sherlock Holmes": "Holmes deductive evidence with specific anomalies",
            "Lupin": "Lupin contrarian inversion with supporting evidence",
        }
        client = make_mock_client(response_map=response_map)
        engine = DeliberationEngine(client, config, personas)

        await engine.run("Test question", "balanced")

        # Calls 6-10 are Round 2 (calls 1-5 are Round 1)
        calls = client.messages.stream.call_args_list
        round2_calls = calls[5:10]  # 5 Round 2 calls after 5 Round 1 calls

        for call in round2_calls:
            prompt = call.kwargs["messages"][0]["content"]
            assert "THIS IS ROUND 2" in prompt
            # Full output should be present, not just 1-2 sentence summaries
            assert "Socrates full analysis with detailed challenges and questions" in prompt
            assert "Occam thorough razor analysis with evidence chains" in prompt

    @pytest.mark.asyncio
    async def test_round2_prompt_not_lossy(self, config: Config, personas: dict[str, Persona]) -> None:
        """Verify Round 2 does NOT use compressed summaries."""
        long_output = "A" * 500  # Simulate substantial output
        client = make_mock_client(default=long_output)
        engine = DeliberationEngine(client, config, personas)

        await engine.run("Test question", "balanced")

        calls = client.messages.stream.call_args_list
        # Check a Round 2 call has the full 500-char output
        round2_call = calls[5]
        prompt = round2_call.kwargs["messages"][0]["content"]
        assert long_output in prompt


class TestEventEmission:
    """AC-4: Events emitted in correct order."""

    @pytest.mark.asyncio
    async def test_event_order_quick_preset(self, config: Config, personas: dict[str, Persona]) -> None:
        """Quick: deliberation_started → round(1) → 3 agents → editorial → 2 editors → done."""
        events: list[DeliberationEvent] = []

        async def collect_event(event: DeliberationEvent) -> None:
            events.append(event)

        client = make_mock_client()
        engine = DeliberationEngine(client, config, personas, on_event=collect_event)

        await engine.run("Test question", "quick")

        event_types = [e.type for e in events]

        # Check structure
        assert event_types[0] == "deliberation_started"
        assert event_types[1] == "round_started"
        assert event_types[-1] == "deliberation_completed"
        assert event_types[-2] == "editorial_completed"

        # Count agent events
        agent_started = [e for e in events if e.type == "agent_started"]
        agent_completed = [e for e in events if e.type == "agent_completed"]
        assert len(agent_started) == 5  # 3 analysts + 2 editors
        assert len(agent_completed) == 5

    @pytest.mark.asyncio
    async def test_sync_callback_also_works(self, config: Config, personas: dict[str, Persona]) -> None:
        """Event callback can be a sync function too."""
        events: list[str] = []

        def sync_callback(event: DeliberationEvent) -> None:
            events.append(event.type)

        client = make_mock_client()
        engine = DeliberationEngine(client, config, personas, on_event=sync_callback)

        await engine.run("Test question", "quick")

        assert "deliberation_started" in events
        assert "deliberation_completed" in events


class TestStreamingCallback:
    """AC-5: Streaming text callback."""

    @pytest.mark.asyncio
    async def test_text_callback_receives_chunks(self, config: Config, personas: dict[str, Persona]) -> None:
        """on_text receives incremental text chunks."""
        text_chunks: list[tuple[str, str]] = []

        async def on_text(agent_name: str, text: str) -> None:
            text_chunks.append((agent_name, text))

        client = make_mock_client(default="Hello world from agent")
        engine = DeliberationEngine(client, config, personas, on_text=on_text)

        await engine.run("Test question", "quick")

        # Should have received multiple chunks from multiple agents
        assert len(text_chunks) > 0
        # Check we got chunks from different agents
        agent_names = {name for name, _ in text_chunks}
        assert len(agent_names) > 1


class TestSamenvatterReceivesEverything:
    """Samenvatter should receive all analyst + editor output."""

    @pytest.mark.asyncio
    async def test_samenvatter_prompt_has_all_output(self, config: Config, personas: dict[str, Persona]) -> None:
        """The samenvatter receives everything."""
        response_map = {
            "Karl Marx": "Marx blind spots analysis",
            "Georg Hegel": "Hegel dialectical synthesis",
            "Hannah Arendt": "Arendt mechanism discovery",
        }
        client = make_mock_client(response_map=response_map)
        engine = DeliberationEngine(client, config, personas)

        await engine.run("Test question", "balanced")

        calls = client.messages.stream.call_args_list
        # Samenvatter is the last call
        samenvatter_call = calls[-1]
        prompt = samenvatter_call.kwargs["messages"][0]["content"]

        # Should contain analyst output (from compiled rounds)
        assert "Round 1" in prompt
        assert "Round 2" in prompt
        # Should contain prior editor output
        assert "Marx blind spots analysis" in prompt
        assert "Hegel dialectical synthesis" in prompt
        assert "Arendt mechanism discovery" in prompt


class TestDefaultPreset:
    """Engine uses default preset when none specified."""

    @pytest.mark.asyncio
    async def test_uses_default_from_config(self, config: Config, personas: dict[str, Persona]) -> None:
        client = make_mock_client()
        engine = DeliberationEngine(client, config, personas)

        result = await engine.run("Test question")  # No preset specified

        assert result.preset.name == "balanced"  # default_preset in config.yaml

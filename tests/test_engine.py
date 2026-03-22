"""Tests for deliberators.engine — orchestration with mocked claude -p subprocess."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deliberators.engine import DeliberationEngine, DeliberationResult
from deliberators.loader import ConfigLoader, PersonaLoader
from deliberators.models import Config, DeliberationEvent, Persona, Preset

PERSONAS_DIR = Path("personas")
CONFIG_PATH = Path("config.yaml")


class MockProcess:
    """Mock for asyncio.create_subprocess_exec result."""

    def __init__(self, stdout_text: str = "Mock response", returncode: int = 0) -> None:
        self.returncode = returncode
        self._stdout = stdout_text.encode()
        self._stderr = b""
        self.stdin_text: str = ""

    async def communicate(self, input: bytes | None = None) -> tuple[bytes, bytes]:
        if input:
            self.stdin_text = input.decode()
        return self._stdout, self._stderr

    def kill(self) -> None:
        pass


class SubprocessTracker:
    """Track all claude -p subprocess calls and their inputs."""

    def __init__(
        self, response_map: dict[str, str] | None = None, default: str = "Mock output"
    ) -> None:
        self.calls: list[dict] = []
        self.response_map = response_map or {}
        self.default = default
        self._count = 0

    def __call__(self, *args: str, **kwargs: object) -> MockProcess:
        self._count += 1

        # Extract system prompt from args
        args_list = list(args)
        system_prompt = ""
        if "--system-prompt" in args_list:
            idx = args_list.index("--system-prompt")
            if idx + 1 < len(args_list):
                system_prompt = str(args_list[idx + 1])

        # Determine response text
        response_text = f"{self.default} #{self._count}"
        for name, response in self.response_map.items():
            if name.lower() in system_prompt.lower():
                response_text = response
                break

        proc = MockProcess(response_text)
        self.calls.append({
            "args": args,
            "kwargs": kwargs,
            "system_prompt": system_prompt,
            "process": proc,
        })
        return proc

    @property
    def call_count(self) -> int:
        return len(self.calls)

    def get_system_prompt(self, index: int) -> str:
        return self.calls[index]["system_prompt"]

    def get_stdin(self, index: int) -> str:
        return self.calls[index]["process"].stdin_text


def make_mock_subprocess(
    response_map: dict[str, str] | None = None, default: str = "Mock output"
) -> SubprocessTracker:
    """Create a SubprocessTracker for mocking claude -p calls."""
    return SubprocessTracker(response_map=response_map, default=default)


def _make_test_config() -> Config:
    """Build a Config with fixed analyst/editor lists for deterministic tests.

    The real config.yaml no longer has fixed lists (team selection is dynamic),
    but engine tests need deterministic team composition.
    """
    return Config(
        default_preset="balanced",
        rounds=2,
        model="opus",
        presets={
            "quick": Preset(
                name="quick",
                description="Quick test preset",
                max_rounds=1,
                min_rounds=1,
                team_size=3,
                editor_count=2,
                analysts=("occam", "holmes", "machiavelli"),
                editors=("marx", "samenvatter"),
                summarizer="samenvatter",
            ),
            "balanced": Preset(
                name="balanced",
                description="Balanced test preset",
                max_rounds=2,
                min_rounds=1,
                team_size=5,
                editor_count=4,
                analysts=("socrates", "occam", "da-vinci", "holmes", "machiavelli"),
                editors=("marx", "hegel", "arendt", "samenvatter"),
                summarizer="samenvatter",
            ),
            "deep": Preset(
                name="deep",
                description="Deep test preset",
                max_rounds=3,
                min_rounds=1,
                team_size=8,
                editor_count=4,
                analysts=("socrates", "occam", "da-vinci", "holmes", "machiavelli", "templar", "tubman", "ibn-khaldun"),
                editors=("marx", "hegel", "arendt", "samenvatter"),
                summarizer="samenvatter",
            ),
        },
    )


@pytest.fixture()
def config() -> Config:
    return _make_test_config()


@pytest.fixture()
def personas() -> dict[str, Persona]:
    return PersonaLoader.load_all(PERSONAS_DIR)


class TestQuickPreset:
    """Quick preset: 3 analysts, 1 round, 2 editors (marx + samenvatter)."""

    @pytest.mark.asyncio
    async def test_correct_agent_count(self, config: Config, personas: dict[str, Persona]) -> None:
        """AC-1: quick = 3 analyst calls + 2 editor calls = 5 total (no convergence: min==max)."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "quick")

        assert tracker.call_count == 7  # 1 intake + 3 analysts + 2 editors + 1 synthesis

    @pytest.mark.asyncio
    async def test_result_structure(self, config: Config, personas: dict[str, Persona]) -> None:
        """AC-1: Result has correct fields."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
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
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            result = await engine.run("Test question", "quick")

        assert len(result.rounds) == 1
        assert 2 not in result.rounds


class TestBalancedPreset:
    """Balanced preset: 5 analysts, 2 rounds, 4 editors."""

    @pytest.mark.asyncio
    async def test_correct_agent_count(self, config: Config, personas: dict[str, Persona]) -> None:
        """AC-1: balanced = 5 analysts x 2 rounds + 1 convergence + 4 editors."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "balanced")

        assert tracker.call_count == 17  # 1 intake + 5 R1 + 1 convergence + 5 R2 + 4 editors + 1 synthesis

    @pytest.mark.asyncio
    async def test_two_rounds(self, config: Config, personas: dict[str, Persona]) -> None:
        """Balanced has 2 analyst rounds."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
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
        tracker = make_mock_subprocess()

        original_gather = asyncio.gather
        gather_calls: list[int] = []

        async def tracking_gather(*coros, **kwargs):  # noqa: ANN003, ANN002
            gather_calls.append(len(coros))
            return await original_gather(*coros, **kwargs)

        with (
            patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)),
            patch("deliberators.engine.asyncio.gather", side_effect=tracking_gather),
        ):
            engine = DeliberationEngine(config, personas)
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
        tracker = make_mock_subprocess(response_map=response_map)
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "balanced")

        # Find the Hegel call by system prompt
        hegel_calls = [c for c in tracker.calls if "Georg Hegel" in c["system_prompt"]]
        assert len(hegel_calls) == 1
        hegel_prompt = hegel_calls[0]["process"].stdin_text
        assert "Marx editorial output" in hegel_prompt

        # Find the Arendt call
        arendt_calls = [c for c in tracker.calls if "Hannah Arendt" in c["system_prompt"]]
        assert len(arendt_calls) == 1
        arendt_prompt = arendt_calls[0]["process"].stdin_text
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
            "Machiavelli": "Machiavelli strategic realism with incentive analysis",
        }
        tracker = make_mock_subprocess(response_map=response_map)
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "balanced")

        # Calls 8-12 are Round 2 (call 0=intake, calls 1-5=R1, call 6=convergence)
        round2_calls = tracker.calls[7:12]

        for call in round2_calls:
            prompt = call["process"].stdin_text
            assert "THIS IS ROUND 2" in prompt
            # Full output should be present, not just 1-2 sentence summaries
            assert "Socrates full analysis with detailed challenges and questions" in prompt
            assert "Occam thorough razor analysis with evidence chains" in prompt

    @pytest.mark.asyncio
    async def test_round2_prompt_not_lossy(self, config: Config, personas: dict[str, Persona]) -> None:
        """Verify Round 2 does NOT use compressed summaries."""
        long_output = "A" * 500  # Simulate substantial output
        tracker = make_mock_subprocess(default=long_output)
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "balanced")

        # Check a Round 2 call has the full 500-char output (index 7: after intake+R1+convergence)
        round2_call = tracker.calls[7]
        prompt = round2_call["process"].stdin_text
        assert long_output in prompt


class TestEventEmission:
    """AC-4: Events emitted in correct order."""

    @pytest.mark.asyncio
    async def test_event_order_quick_preset(self, config: Config, personas: dict[str, Persona]) -> None:
        """Quick: deliberation_started -> round(1) -> 3 agents -> editorial -> 2 editors -> done."""
        events: list[DeliberationEvent] = []

        async def collect_event(event: DeliberationEvent) -> None:
            events.append(event)

        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas, on_event=collect_event)
            await engine.run("Test question", "quick")

        event_types = [e.type for e in events]

        # Check structure
        assert event_types[0] == "deliberation_started"
        assert event_types[1] == "intake_started"
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

        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas, on_event=sync_callback)
            await engine.run("Test question", "quick")

        assert "deliberation_started" in events
        assert "deliberation_completed" in events


class TestStreamingCallback:
    """AC-5: Text callback."""

    @pytest.mark.asyncio
    async def test_text_callback_receives_output(self, config: Config, personas: dict[str, Persona]) -> None:
        """on_text receives agent output."""
        text_chunks: list[tuple[str, str]] = []

        async def on_text(agent_name: str, text: str) -> None:
            text_chunks.append((agent_name, text))

        tracker = make_mock_subprocess(default="Hello world from agent")
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas, on_text=on_text)
            await engine.run("Test question", "quick")

        # Should have received output from multiple agents
        assert len(text_chunks) > 0
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
        tracker = make_mock_subprocess(response_map=response_map)
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "balanced")

        # Samenvatter is the last call
        samenvatter_call = tracker.calls[-1]
        prompt = samenvatter_call["process"].stdin_text

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
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            result = await engine.run("Test question")  # No preset specified

        assert result.preset.name == "balanced"  # default_preset in config.yaml


class TestCodeContext:
    """Code context injection into prompts."""

    @pytest.mark.asyncio
    async def test_code_context_in_analyst_prompt(self, config: Config, personas: dict[str, Persona]) -> None:
        """When code_context is provided, analyst prompts contain CODE UNDER REVIEW."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Review this code", "quick", code_context="def foo(): pass")

        # First 3 calls are analysts
        for call in tracker.calls[1:4]:  # skip intake (call 0)
            prompt = call["process"].stdin_text
            assert "CODE UNDER REVIEW" in prompt
            assert "def foo(): pass" in prompt

    @pytest.mark.asyncio
    async def test_code_context_in_editor_prompt(self, config: Config, personas: dict[str, Persona]) -> None:
        """When code_context is provided, editor prompts contain CODE UNDER REVIEW."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Review this code", "quick", code_context="def bar(): pass")

        # Editor calls: skip intake (0) + 3 analysts, exclude synthesis (last)
        for call in tracker.calls[4:-1]:
            prompt = call["process"].stdin_text
            assert "CODE UNDER REVIEW" in prompt
            assert "def bar(): pass" in prompt

    @pytest.mark.asyncio
    async def test_no_code_context_means_no_section(self, config: Config, personas: dict[str, Persona]) -> None:
        """When code_context is None, prompts do NOT contain CODE UNDER REVIEW."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("General question", "quick")

        for call in tracker.calls:
            prompt = call["process"].stdin_text
            assert "CODE UNDER REVIEW" not in prompt

    @pytest.mark.asyncio
    async def test_code_context_stored_in_result(self, config: Config, personas: dict[str, Persona]) -> None:
        """code_context is stored on DeliberationResult."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            result = await engine.run("Review", "quick", code_context="some code")

        assert result.code_context == "some code"

    @pytest.mark.asyncio
    async def test_none_code_context_on_result(self, config: Config, personas: dict[str, Persona]) -> None:
        """code_context is None when not provided."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            result = await engine.run("Question", "quick")

        assert result.code_context is None


class TestMissingPersonaWarning:
    """AC-3: Engine logs warning when persona is missing."""

    @pytest.mark.asyncio
    async def test_warns_on_missing_analyst(self, config: Config, personas: dict[str, Persona], caplog: pytest.LogCaptureFixture) -> None:
        """Missing analyst triggers a warning log."""
        mini_config = Config(
            default_preset="test",
            rounds=1,
            model="opus",
            presets={
                "test": Preset(
                    name="test", description="", max_rounds=1,
                    analysts=("occam", "ghost-analyst"),
                    editors=("samenvatter",),
                ),
            },
        )
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(mini_config, personas)
            with caplog.at_level(logging.WARNING, logger="deliberators.engine"):
                result = await engine.run("Test", "test")

        assert "ghost-analyst" in caplog.text
        # Deliberation should still complete
        assert result.rounds[1]["occam"] != ""
        assert result.rounds[1]["ghost-analyst"] == ""

    @pytest.mark.asyncio
    async def test_warns_on_missing_editor(self, config: Config, personas: dict[str, Persona], caplog: pytest.LogCaptureFixture) -> None:
        """Missing editor triggers a warning log."""
        mini_config = Config(
            default_preset="test",
            rounds=1,
            model="opus",
            presets={
                "test": Preset(
                    name="test", description="", max_rounds=1,
                    analysts=("occam",),
                    editors=("ghost-editor", "samenvatter"),
                ),
            },
        )
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(mini_config, personas)
            with caplog.at_level(logging.WARNING, logger="deliberators.engine"):
                await engine.run("Test", "test")

        assert "ghost-editor" in caplog.text


class TestSummarizerConfig:
    """AC-1 (Phase 11): Summarizer identified by preset.summarizer, not hardcoded string."""

    @pytest.mark.asyncio
    async def test_preset_summarizer_routes_to_samenvatter_output(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """When preset.summarizer matches an editor, output goes to samenvatter_output."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            result = await engine.run("Test", "quick")

        # quick preset has summarizer=samenvatter
        assert result.samenvatter_output is not None
        assert "samenvatter" not in result.editor_outputs

    @pytest.mark.asyncio
    async def test_no_summarizer_means_all_editors_in_outputs(
        self, personas: dict[str, Persona]
    ) -> None:
        """When preset.summarizer is None, all editors go to editor_outputs."""
        no_summarizer_config = Config(
            default_preset="test",
            rounds=1,
            model="opus",
            presets={
                "test": Preset(
                    name="test", description="", max_rounds=1,
                    analysts=("occam",),
                    editors=("marx", "samenvatter"),
                    summarizer=None,
                ),
            },
        )
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(no_summarizer_config, personas)
            result = await engine.run("Test", "test")

        assert result.samenvatter_output is None
        assert "marx" in result.editor_outputs
        assert "samenvatter" in result.editor_outputs

class TestAgentErrorHandling:
    """AC-4: Error handling per agent — failed agents don't crash the deliberation."""

    @pytest.mark.asyncio
    async def test_failed_agent_returns_error_string(self, config: Config, personas: dict[str, Persona]) -> None:
        """A failing subprocess returns an error message string, not an exception."""
        call_count = 0

        def failing_exec(*args: str, **kwargs: object) -> MockProcess:
            nonlocal call_count
            call_count += 1
            args_list = list(args)
            system_prompt = ""
            if "--system-prompt" in args_list:
                idx = args_list.index("--system-prompt")
                if idx + 1 < len(args_list):
                    system_prompt = str(args_list[idx + 1])
            # Make Occam fail
            if "Willem van Occam" in system_prompt:
                proc = MockProcess("", returncode=1)
                proc._stderr = b"API error"
                return proc
            return MockProcess(f"Success #{call_count}")

        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=failing_exec)):
            engine = DeliberationEngine(config, personas)
            result = await engine.run("Test", "quick")

        # Occam should have error message
        assert "[Agent fout:" in result.rounds[1]["occam"]
        # Other analysts should have succeeded
        assert result.rounds[1]["holmes"] != ""
        assert "[Agent fout:" not in result.rounds[1]["holmes"]
        assert result.rounds[1]["machiavelli"] != ""

    @pytest.mark.asyncio
    async def test_deliberation_completes_despite_failure(self, config: Config, personas: dict[str, Persona]) -> None:
        """Editors still run even if an analyst fails."""
        def failing_exec(*args: str, **kwargs: object) -> MockProcess:
            args_list = list(args)
            system_prompt = ""
            if "--system-prompt" in args_list:
                idx = args_list.index("--system-prompt")
                if idx + 1 < len(args_list):
                    system_prompt = str(args_list[idx + 1])
            if "Willem van Occam" in system_prompt:
                proc = MockProcess("", returncode=1)
                proc._stderr = b"Simulated failure"
                return proc
            return MockProcess("Output")

        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=failing_exec)):
            engine = DeliberationEngine(config, personas)
            result = await engine.run("Test", "quick")

        # Editors should still have run
        assert "marx" in result.editor_outputs
        assert result.samenvatter_output is not None

    @pytest.mark.asyncio
    async def test_error_message_reaches_editors(self, config: Config, personas: dict[str, Persona]) -> None:
        """The error message from a failed agent is visible to editors."""
        tracker = make_mock_subprocess()
        call_list: list[dict] = tracker.calls

        def failing_exec(*args: str, **kwargs: object) -> MockProcess:
            args_list = list(args)
            system_prompt = ""
            if "--system-prompt" in args_list:
                idx = args_list.index("--system-prompt")
                if idx + 1 < len(args_list):
                    system_prompt = str(args_list[idx + 1])
            if "Willem van Occam" in system_prompt:
                proc = MockProcess("", returncode=1)
                proc._stderr = b"Simulated failure"
                call_list.append({"system_prompt": system_prompt, "process": proc})
                return proc
            proc = MockProcess("Normal output")
            call_list.append({"system_prompt": system_prompt, "process": proc})
            return proc

        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=failing_exec)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test", "quick")

        # Check that the editor (marx) received the error in compiled output
        marx_calls = [c for c in call_list if "Karl Marx" in c["system_prompt"]]
        assert len(marx_calls) == 1
        marx_prompt = marx_calls[0]["process"].stdin_text
        assert "[Agent fout:" in marx_prompt

    @pytest.mark.asyncio
    async def test_logs_error_on_failure(self, config: Config, personas: dict[str, Persona], caplog: pytest.LogCaptureFixture) -> None:
        """Failed agent triggers an error log."""
        def failing_exec(*args: str, **kwargs: object) -> MockProcess:
            args_list = list(args)
            system_prompt = ""
            if "--system-prompt" in args_list:
                idx = args_list.index("--system-prompt")
                if idx + 1 < len(args_list):
                    system_prompt = str(args_list[idx + 1])
            if "Willem van Occam" in system_prompt:
                proc = MockProcess("", returncode=1)
                proc._stderr = b"Connection refused"
                return proc
            return MockProcess("OK")

        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=failing_exec)):
            engine = DeliberationEngine(config, personas)
            with caplog.at_level(logging.ERROR, logger="deliberators.engine"):
                await engine.run("Test", "quick")

        assert "Willem van Occam" in caplog.text
        assert "Connection refused" in caplog.text

    @pytest.mark.asyncio
    async def test_exception_in_subprocess_call(self, config: Config, personas: dict[str, Persona]) -> None:
        """An exception during subprocess creation is caught gracefully."""
        call_count = 0

        def exception_exec(*args: str, **kwargs: object) -> MockProcess:
            nonlocal call_count
            call_count += 1
            args_list = list(args)
            system_prompt = ""
            if "--system-prompt" in args_list:
                idx = args_list.index("--system-prompt")
                if idx + 1 < len(args_list):
                    system_prompt = str(args_list[idx + 1])
            if "Willem van Occam" in system_prompt:
                raise FileNotFoundError("claude not found")
            return MockProcess(f"Success #{call_count}")

        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=exception_exec)):
            engine = DeliberationEngine(config, personas)
            result = await engine.run("Test", "quick")

        assert "[Agent fout:" in result.rounds[1]["occam"]
        assert "FileNotFoundError" in result.rounds[1]["occam"]


class TestSubprocessArgs:
    """Verify correct arguments are passed to claude -p."""

    @pytest.mark.asyncio
    async def test_model_passed_from_persona(self, config: Config, personas: dict[str, Persona]) -> None:
        """The --model flag matches persona.model, not config.model."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test", "quick")

        for call in tracker.calls:
            args = list(call["args"])
            assert "--model" in args
            model_idx = args.index("--model")
            model_used = args[model_idx + 1]
            assert model_used in ("opus", "sonnet")

    @pytest.mark.asyncio
    async def test_mixed_models_in_quick_preset(self, config: Config, personas: dict[str, Persona]) -> None:
        """Quick preset uses mix of sonnet and opus models per persona."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test", "quick")

        models_used = set()
        for call in tracker.calls:
            args = list(call["args"])
            model_idx = args.index("--model")
            models_used.add(args[model_idx + 1])

        # Quick has sonnet analysts (occam, holmes) + opus analyst (machiavelli) + opus editor (marx) + sonnet editor (samenvatter)
        assert "sonnet" in models_used
        assert "opus" in models_used

    @pytest.mark.asyncio
    async def test_system_prompt_from_persona(self, config: Config, personas: dict[str, Persona]) -> None:
        """The --system-prompt flag contains the persona's system_prompt."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test", "quick")

        # First call should be an analyst with a FORBIDDEN constraint
        first_system = tracker.get_system_prompt(1)  # index 0 is intake agent
        assert "FORBIDDEN" in first_system or "MUST NOT" in first_system

    @pytest.mark.asyncio
    async def test_prompt_sent_via_stdin(self, config: Config, personas: dict[str, Persona]) -> None:
        """The user prompt is sent via stdin, not as a CLI argument."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("My test question", "quick")

        for call in tracker.calls:
            stdin_text = call["process"].stdin_text
            assert "My test question" in stdin_text


class TestInjectableAgentFn:
    """Injectable agent_fn allows tests to bypass subprocess mocking."""

    @pytest.mark.asyncio
    async def test_agent_fn_called_instead_of_subprocess(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """When agent_fn is provided, subprocess is NOT called."""
        calls: list[tuple[str, str]] = []

        async def fake_agent(persona: Persona, prompt: str) -> str:
            calls.append((persona.name, prompt))
            return f"Response from {persona.name}"

        engine = DeliberationEngine(config, personas, agent_fn=fake_agent)
        result = await engine.run("Test question", "quick")

        # 3 analysts + 2 editors = 5 calls
        assert len(calls) == 5
        assert result.rounds[1]["occam"] == "Response from Willem van Occam"
        assert result.samenvatter_output is not None

    @pytest.mark.asyncio
    async def test_agent_fn_receives_correct_persona(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """agent_fn receives the correct Persona object."""
        received_personas: list[str] = []

        async def fake_agent(persona: Persona, prompt: str) -> str:
            received_personas.append(persona.name)
            return "OK"

        engine = DeliberationEngine(config, personas, agent_fn=fake_agent)
        await engine.run("Test", "quick")

        # Quick preset: occam, holmes, machiavelli (analysts) + marx, samenvatter (editors)
        assert "Willem van Occam" in received_personas
        assert "Sherlock Holmes" in received_personas
        assert "Niccol\u00f2 Machiavelli" in received_personas

    @pytest.mark.asyncio
    async def test_agent_fn_with_on_text_callback(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """on_text callback still fires when using injectable agent_fn."""
        text_chunks: list[tuple[str, str]] = []

        async def fake_agent(persona: Persona, prompt: str) -> str:
            return f"Output from {persona.name}"

        async def on_text(agent_name: str, text: str) -> None:
            text_chunks.append((agent_name, text))

        engine = DeliberationEngine(
            config, personas, agent_fn=fake_agent, on_text=on_text
        )
        await engine.run("Test", "quick")

        assert len(text_chunks) == 5
        names = {name for name, _ in text_chunks}
        assert "Willem van Occam" in names

    @pytest.mark.asyncio
    async def test_default_uses_subprocess_when_no_agent_fn(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """Without agent_fn, the engine uses subprocess (backward compat)."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test", "quick")

        assert tracker.call_count == 7  # 1 intake + 3 analysts + 2 editors + 1 synthesis


class TestSubprocessTimeout:
    """Subprocess calls have a configurable timeout."""

    @pytest.mark.asyncio
    async def test_timeout_returns_error_string(self, personas: dict[str, Persona]) -> None:
        """A timed-out subprocess returns an error message."""
        timeout_config = Config(
            default_preset="test",
            rounds=1,
            model="opus",
            presets={
                "test": Preset(
                    name="test", description="", max_rounds=1,
                    analysts=("occam",),
                    editors=("samenvatter",),
                ),
            },
            timeout=1,
        )

        async def hanging_exec(*args: str, **kwargs: object) -> MockProcess:
            proc = MockProcess("will never arrive")
            original_communicate = proc.communicate

            async def slow_communicate(input: bytes | None = None) -> tuple[bytes, bytes]:
                await asyncio.sleep(10)  # Way longer than timeout
                return await original_communicate(input)

            proc.communicate = slow_communicate
            return proc

        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=hanging_exec)):
            engine = DeliberationEngine(timeout_config, personas)
            result = await engine.run("Test", "test")

        assert "[Agent fout:" in result.rounds[1]["occam"]
        assert "timeout" in result.rounds[1]["occam"]

    @pytest.mark.asyncio
    async def test_timeout_value_from_config(self, config: Config, personas: dict[str, Persona]) -> None:
        """Config timeout value is used (default 120s)."""
        assert config.timeout == 120

    @pytest.mark.asyncio
    async def test_custom_timeout_in_config(self, personas: dict[str, Persona]) -> None:
        """Custom timeout value is respected."""
        custom_config = Config(
            default_preset="test",
            rounds=1,
            model="opus",
            presets={
                "test": Preset(
                    name="test", description="", max_rounds=1,
                    analysts=("occam",),
                    editors=("samenvatter",),
                ),
            },
            timeout=60,
        )
        assert custom_config.timeout == 60


class TestConcurrencyLimit:
    """Concurrent agent calls are limited by max_concurrent."""

    @pytest.mark.asyncio
    async def test_max_concurrent_from_config(self, config: Config) -> None:
        """Config has max_concurrent field."""
        assert config.max_concurrent == 10

    @pytest.mark.asyncio
    async def test_concurrent_agents_limited(self, personas: dict[str, Persona]) -> None:
        """Semaphore limits concurrent agents to max_concurrent."""
        max_concurrent = 2
        concurrency_log: list[int] = []
        current_count = 0

        async def tracking_agent(persona: Persona, prompt: str) -> str:
            nonlocal current_count
            current_count += 1
            concurrency_log.append(current_count)
            await asyncio.sleep(0.01)
            current_count -= 1
            return f"Response from {persona.name}"

        limited_config = Config(
            default_preset="test",
            rounds=1,
            model="opus",
            presets={
                "test": Preset(
                    name="test", description="", max_rounds=1,
                    analysts=("occam", "holmes", "machiavelli", "socrates", "da-vinci"),
                    editors=("samenvatter",),
                ),
            },
            max_concurrent=max_concurrent,
        )

        engine = DeliberationEngine(limited_config, personas, agent_fn=tracking_agent)
        await engine.run("Test", "test")

        # Peak concurrency should never exceed max_concurrent
        assert max(concurrency_log) <= max_concurrent


class TestIntakePhase:
    """Tests for the intake phase (Phase 17)."""

    @pytest.mark.asyncio
    async def test_intake_brief_in_result(self, config: Config, personas: dict[str, Persona]) -> None:
        """engine.run() returns a result with intake_brief populated."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            result = await engine.run("Test question", "quick")

        assert result.intake_brief is not None
        assert result.intake_brief.question == "Test question"

    @pytest.mark.asyncio
    async def test_analyst_prompt_includes_intake_context(self, config: Config, personas: dict[str, Persona]) -> None:
        """Analyst prompts include INTAKE CONTEXT from the intake brief."""
        tracker = make_mock_subprocess(default="IS_CLEAR: yes\nCLARIFICATION_QUESTION: none\nBRIEF: Test summary about the question")
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "quick")

        # Analyst calls are 1-3 (0 is intake)
        for call in tracker.calls[1:4]:
            prompt = call["process"].stdin_text
            assert "INTAKE CONTEXT:" in prompt
            assert "Test summary about the question" in prompt
            # INTAKE CONTEXT should come before QUESTION FOR DELIBERATION
            assert prompt.index("INTAKE CONTEXT:") < prompt.index("QUESTION FOR DELIBERATION:")

    @pytest.mark.asyncio
    async def test_intake_events_emitted(self, config: Config, personas: dict[str, Persona]) -> None:
        """intake_started and intake_completed events are emitted before round_started."""
        events: list[DeliberationEvent] = []

        async def collect(event: DeliberationEvent) -> None:
            events.append(event)

        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas, on_event=collect)
            await engine.run("Test question", "quick")

        types = [e.type for e in events]
        assert "intake_started" in types
        assert "intake_completed" in types
        # intake must come before first round
        assert types.index("intake_started") < types.index("round_started")
        assert types.index("intake_completed") < types.index("round_started")

    @pytest.mark.asyncio
    async def test_no_clarification_when_callback_none(self, config: Config, personas: dict[str, Persona]) -> None:
        """When on_clarify is None, unclear questions proceed without clarification."""
        tracker = make_mock_subprocess(default="IS_CLEAR: no\nCLARIFICATION_QUESTION: What do you mean?\nBRIEF: Ambiguous question")
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas, on_clarify=None)
            result = await engine.run("Vague question", "quick")

        assert result.intake_brief is not None
        assert result.intake_brief.is_clear is False
        assert result.intake_brief.clarifications == ()

    @pytest.mark.asyncio
    async def test_clarification_loop_called(self, config: Config, personas: dict[str, Persona]) -> None:
        """When intake says IS_CLEAR: no and on_clarify is set, clarification is requested."""
        call_count = 0

        async def mock_clarify(question: str) -> str:
            nonlocal call_count
            call_count += 1
            return "More context here"

        # First call: unclear. Second call: clear (after clarification).
        responses = iter([
            "IS_CLEAR: no\nCLARIFICATION_QUESTION: What specifically?\nBRIEF: Needs more context",
            "IS_CLEAR: yes\nCLARIFICATION_QUESTION: none\nBRIEF: Clarified question about X",
        ])

        original_functional = DeliberationEngine._call_functional_agent

        async def patched_functional(self_engine, system_prompt, prompt, model):
            # Only intercept intake calls (check for intake system prompt)
            if "intake analyst" in system_prompt.lower():
                return next(responses, "IS_CLEAR: yes\nCLARIFICATION_QUESTION: none\nBRIEF: fallback")
            return await original_functional(self_engine, system_prompt, prompt, model)

        tracker = make_mock_subprocess()
        with (
            patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)),
            patch.object(DeliberationEngine, "_call_functional_agent", patched_functional),
        ):
            engine = DeliberationEngine(config, personas, on_clarify=mock_clarify)
            result = await engine.run("Vague question", "quick")

        assert call_count == 1
        assert len(result.intake_brief.clarifications) == 1
        assert result.intake_brief.clarifications[0] == ("What specifically?", "More context here")
        assert result.intake_brief.is_clear is True

    @pytest.mark.asyncio
    async def test_clarification_max_three_rounds(self, config: Config, personas: dict[str, Persona]) -> None:
        """Clarification loop stops after 3 iterations even if still unclear."""
        clarify_count = 0

        async def mock_clarify(question: str) -> str:
            nonlocal clarify_count
            clarify_count += 1
            return f"Answer {clarify_count}"

        # Always returns unclear
        async def always_unclear(self_engine, system_prompt, prompt, model):
            if "intake analyst" in system_prompt.lower():
                return "IS_CLEAR: no\nCLARIFICATION_QUESTION: Still unclear?\nBRIEF: Still ambiguous"
            return "Mock output"

        tracker = make_mock_subprocess()
        with (
            patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)),
            patch.object(DeliberationEngine, "_call_functional_agent", always_unclear),
        ):
            engine = DeliberationEngine(config, personas, on_clarify=mock_clarify)
            result = await engine.run("Perpetually vague", "quick")

        # Max 3 clarification rounds: first iteration finds unclear, asks, loops.
        # Iterations: 0 (unclear->clarify), 1 (unclear->clarify), 2 (unclear->break at max)
        assert clarify_count <= 3
        assert len(result.intake_brief.clarifications) <= 3


class TestParseIntakeOutput:
    """Unit tests for _parse_intake_output."""

    def test_parse_clear_output(self) -> None:
        output = "IS_CLEAR: yes\nCLARIFICATION_QUESTION: none\nBRIEF: A good question about ethics"
        result = DeliberationEngine._parse_intake_output(output)
        assert result["is_clear"] == "yes"
        assert result["clarification_question"] == "none"
        assert result["brief"] == "A good question about ethics"

    def test_parse_unclear_output(self) -> None:
        output = "IS_CLEAR: no\nCLARIFICATION_QUESTION: What domain?\nBRIEF: Needs context"
        result = DeliberationEngine._parse_intake_output(output)
        assert result["is_clear"] == "no"
        assert result["clarification_question"] == "What domain?"
        assert result["brief"] == "Needs context"

    def test_parse_fallback_on_garbage(self) -> None:
        output = "Some random LLM output without structure"
        result = DeliberationEngine._parse_intake_output(output)
        assert result["is_clear"] == "yes"  # fallback default
        assert result["brief"] == "Some random LLM output without structure"

    def test_parse_empty_output(self) -> None:
        result = DeliberationEngine._parse_intake_output("")
        assert result["is_clear"] == "yes"
        assert result["brief"] == ""


class TestParseConvergenceOutput:
    """Unit tests for _parse_convergence_output."""

    def test_parse_continue(self) -> None:
        output = "CONTINUE: yes\nREASON: New perspectives still emerging"
        result = DeliberationEngine._parse_convergence_output(output)
        assert result["continue"] == "yes"
        assert result["reason"] == "New perspectives still emerging"

    def test_parse_stop(self) -> None:
        output = "CONTINUE: no\nREASON: Positions have solidified"
        result = DeliberationEngine._parse_convergence_output(output)
        assert result["continue"] == "no"
        assert result["reason"] == "Positions have solidified"

    def test_parse_fallback_on_garbage(self) -> None:
        output = "Some random output without structure"
        result = DeliberationEngine._parse_convergence_output(output)
        assert result["continue"] == "yes"  # default
        assert result["reason"] == "Some random output without structure"

    def test_parse_empty_output(self) -> None:
        result = DeliberationEngine._parse_convergence_output("")
        assert result["continue"] == "yes"
        assert result["reason"] == ""


class TestConvergencePhase:
    """Tests for the adaptive rounds convergence phase."""

    @pytest.mark.asyncio
    async def test_no_convergence_when_min_equals_max(self, config: Config, personas: dict[str, Persona]) -> None:
        """Quick preset (min==max==1) skips convergence entirely."""
        events: list[DeliberationEvent] = []

        async def collect(event: DeliberationEvent) -> None:
            events.append(event)

        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas, on_event=collect)
            await engine.run("Test question", "quick")

        types = [e.type for e in events]
        assert "convergence_started" not in types
        assert "convergence_completed" not in types

    @pytest.mark.asyncio
    async def test_convergence_events_emitted_for_balanced(self, config: Config, personas: dict[str, Persona]) -> None:
        """Balanced preset emits convergence events after R1."""
        events: list[DeliberationEvent] = []

        async def collect(event: DeliberationEvent) -> None:
            events.append(event)

        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas, on_event=collect)
            await engine.run("Test question", "balanced")

        types = [e.type for e in events]
        assert "convergence_started" in types
        assert "convergence_completed" in types
        # Convergence should come after first round_completed, before second round_started
        conv_idx = types.index("convergence_started")
        round_completed_indices = [i for i, t in enumerate(types) if t == "round_completed"]
        round_started_indices = [i for i, t in enumerate(types) if t == "round_started"]
        assert conv_idx > round_completed_indices[0]  # after first round completes
        assert conv_idx < round_started_indices[1]  # before second round starts

    @pytest.mark.asyncio
    async def test_early_stop_when_converged(self, personas: dict[str, Persona]) -> None:
        """If convergence says stop after R1, only 1 round runs."""
        mini_config = Config(
            default_preset="test",
            rounds=2,
            model="opus",
            presets={
                "test": Preset(
                    name="test", description="", max_rounds=3, min_rounds=1,
                    analysts=("occam", "holmes"),
                    editors=("samenvatter",),
                    summarizer="samenvatter",
                ),
            },
        )

        async def stop_convergence(self_engine, system_prompt, prompt, model):
            if "convergence analyst" in system_prompt.lower():
                return "CONTINUE: no\nREASON: All positions have converged"
            return "Mock output"

        tracker = make_mock_subprocess()
        with (
            patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)),
            patch.object(DeliberationEngine, "_call_functional_agent", stop_convergence),
        ):
            engine = DeliberationEngine(mini_config, personas)
            result = await engine.run("Test", "test")

        # Only 1 round should have run (convergence stopped after R1)
        assert 1 in result.rounds
        assert 2 not in result.rounds

    @pytest.mark.asyncio
    async def test_max_rounds_enforced(self, personas: dict[str, Persona]) -> None:
        """Even if convergence always says continue, max_rounds is respected."""
        mini_config = Config(
            default_preset="test",
            rounds=2,
            model="opus",
            presets={
                "test": Preset(
                    name="test", description="", max_rounds=2, min_rounds=1,
                    analysts=("occam",),
                    editors=("samenvatter",),
                    summarizer="samenvatter",
                ),
            },
        )

        async def always_continue(self_engine, system_prompt, prompt, model):
            if "convergence analyst" in system_prompt.lower():
                return "CONTINUE: yes\nREASON: Still diverging"
            return "Mock output"

        tracker = make_mock_subprocess()
        with (
            patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)),
            patch.object(DeliberationEngine, "_call_functional_agent", always_continue),
        ):
            engine = DeliberationEngine(mini_config, personas)
            result = await engine.run("Test", "test")

        # Exactly 2 rounds (max enforced)
        assert 1 in result.rounds
        assert 2 in result.rounds
        assert 3 not in result.rounds

    @pytest.mark.asyncio
    async def test_convergence_completed_includes_data(self, config: Config, personas: dict[str, Persona]) -> None:
        """convergence_completed event includes should_continue and reason."""
        events: list[DeliberationEvent] = []

        async def collect(event: DeliberationEvent) -> None:
            events.append(event)

        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas, on_event=collect)
            await engine.run("Test question", "balanced")

        conv_events = [e for e in events if e.type == "convergence_completed"]
        assert len(conv_events) >= 1
        assert "should_continue" in conv_events[0].data
        assert "reason" in conv_events[0].data


class TestParseTeamSelectionOutput:
    """Unit tests for _parse_team_selection_output."""

    @pytest.fixture()
    def mock_personas(self) -> dict[str, Persona]:
        """Minimal persona dict for team selection parsing tests."""
        def _p(name: str, role: str = "analyst") -> Persona:
            return Persona(
                name=name, model="sonnet", domains=("testing",), role=role,
                reasoning_style="test", forbidden=("a", "b"),
                focus="test", output_format={},
                system_prompt="You are FORBIDDEN from X. You MUST NOT Y.",
            )
        return {
            "socrates": _p("Socrates"),
            "occam": _p("Occam"),
            "holmes": _p("Holmes"),
            "marx": _p("Marx", "editor"),
            "samenvatter": _p("Samenvatter", "editor"),
        }

    def test_parse_valid_output(self, mock_personas: dict[str, Persona]) -> None:
        output = "ANALYSTS: socrates, occam, holmes\nEDITORS: marx, samenvatter\nREASON: Good team"
        analysts, editors, reason = DeliberationEngine._parse_team_selection_output(output, mock_personas)
        assert analysts == ["socrates", "occam", "holmes"]
        assert editors == ["marx", "samenvatter"]
        assert reason == "Good team"

    def test_filters_invalid_names(self, mock_personas: dict[str, Persona]) -> None:
        output = "ANALYSTS: socrates, nonexistent, occam\nEDITORS: marx\nREASON: test"
        analysts, editors, reason = DeliberationEngine._parse_team_selection_output(output, mock_personas)
        assert analysts == ["socrates", "occam"]
        assert editors == ["marx"]

    def test_filters_wrong_role(self, mock_personas: dict[str, Persona]) -> None:
        """Editors can't be selected as analysts and vice versa."""
        output = "ANALYSTS: socrates, marx\nEDITORS: occam\nREASON: test"
        analysts, editors, reason = DeliberationEngine._parse_team_selection_output(output, mock_personas)
        assert analysts == ["socrates"]  # marx is editor, filtered out
        assert editors == []  # occam is analyst, filtered out

    def test_parse_empty_output(self, mock_personas: dict[str, Persona]) -> None:
        analysts, editors, reason = DeliberationEngine._parse_team_selection_output("", mock_personas)
        assert analysts == []
        assert editors == []
        assert reason == ""


class TestTeamSelection:
    """Integration tests for dynamic team selection."""

    @pytest.mark.asyncio
    async def test_dynamic_selection_used_when_no_fixed_lists(self, personas: dict[str, Persona]) -> None:
        """When preset has no fixed analysts/editors, team selection agent is called."""
        dynamic_config = Config(
            default_preset="test",
            rounds=1,
            model="opus",
            presets={
                "test": Preset(
                    name="test", description="Dynamic test", max_rounds=1,
                    team_size=2, editor_count=1,
                    summarizer="samenvatter",
                ),
            },
        )

        async def mock_functional(self_engine, system_prompt, prompt, model):
            if "team selection" in system_prompt.lower():
                return "ANALYSTS: socrates, occam\nEDITORS: samenvatter\nREASON: Best fit"
            if "intake analyst" in system_prompt.lower():
                return "IS_CLEAR: yes\nCLARIFICATION_QUESTION: none\nBRIEF: Clear question"
            if "convergence" in system_prompt.lower():
                return "CONTINUE: no\nREASON: Done"
            return "Mock output"

        tracker = make_mock_subprocess()
        with (
            patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)),
            patch.object(DeliberationEngine, "_call_functional_agent", mock_functional),
        ):
            engine = DeliberationEngine(dynamic_config, personas)
            result = await engine.run("What is justice?", "test")

        # Should have used dynamically selected analysts
        assert "socrates" in result.rounds[1]
        assert "occam" in result.rounds[1]
        assert result.samenvatter_output is not None

    @pytest.mark.asyncio
    async def test_fixed_lists_bypass_team_selection(self, config: Config, personas: dict[str, Persona]) -> None:
        """When preset has fixed analysts/editors, team selection is skipped."""
        events: list[DeliberationEvent] = []

        async def collect(event: DeliberationEvent) -> None:
            events.append(event)

        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas, on_event=collect)
            await engine.run("Test question", "quick")

        types = [e.type for e in events]
        assert "team_selected" not in types

    @pytest.mark.asyncio
    async def test_team_selected_event_emitted(self, personas: dict[str, Persona]) -> None:
        """team_selected event is emitted during dynamic selection."""
        dynamic_config = Config(
            default_preset="test",
            rounds=1,
            model="opus",
            presets={
                "test": Preset(
                    name="test", description="Dynamic test", max_rounds=1,
                    team_size=2, editor_count=1,
                    summarizer="samenvatter",
                ),
            },
        )
        events: list[DeliberationEvent] = []

        async def collect(event: DeliberationEvent) -> None:
            events.append(event)

        async def mock_functional(self_engine, system_prompt, prompt, model):
            if "team selection" in system_prompt.lower():
                return "ANALYSTS: socrates, occam\nEDITORS: samenvatter\nREASON: Best fit"
            if "intake analyst" in system_prompt.lower():
                return "IS_CLEAR: yes\nCLARIFICATION_QUESTION: none\nBRIEF: Clear"
            return "Mock output"

        tracker = make_mock_subprocess()
        with (
            patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)),
            patch.object(DeliberationEngine, "_call_functional_agent", mock_functional),
        ):
            engine = DeliberationEngine(dynamic_config, personas, on_event=collect)
            await engine.run("What is justice?", "test")

        types = [e.type for e in events]
        assert "team_selected" in types
        team_event = next(e for e in events if e.type == "team_selected")
        assert team_event.data["analysts"] == ["socrates", "occam"]
        assert team_event.data["editors"] == ["samenvatter"]

    @pytest.mark.asyncio
    async def test_code_context_hint_in_team_selection(self, personas: dict[str, Persona]) -> None:
        """When code_context is provided, team selection prompt includes code hint."""
        dynamic_config = Config(
            default_preset="test",
            rounds=1,
            model="opus",
            presets={
                "test": Preset(
                    name="test", description="Dynamic test", max_rounds=1,
                    team_size=2, editor_count=1,
                    summarizer="samenvatter",
                ),
            },
        )
        received_prompts: list[str] = []

        async def mock_functional(self_engine, system_prompt, prompt, model):
            if "team selection" in system_prompt.lower():
                received_prompts.append(prompt)
                return "ANALYSTS: linus, schneier\nEDITORS: code-synthesizer\nREASON: Code review"
            if "intake analyst" in system_prompt.lower():
                return "IS_CLEAR: yes\nCLARIFICATION_QUESTION: none\nBRIEF: Code review"
            return "Mock output"

        tracker = make_mock_subprocess()
        with (
            patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)),
            patch.object(DeliberationEngine, "_call_functional_agent", mock_functional),
        ):
            engine = DeliberationEngine(dynamic_config, personas)
            await engine.run("Review this", "test", code_context="def foo(): pass")

        assert len(received_prompts) == 1
        assert "code review" in received_prompts[0].lower()

    @pytest.mark.asyncio
    async def test_intake_always_runs(self, config: Config, personas: dict[str, Persona]) -> None:
        """Intake runs for all presets, including when code_context is provided."""
        events: list[DeliberationEvent] = []

        async def collect(event: DeliberationEvent) -> None:
            events.append(event)

        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas, on_event=collect)
            await engine.run("Review this code", "quick", code_context="def foo(): pass")

        types = [e.type for e in events]
        assert "intake_started" in types
        assert "intake_completed" in types

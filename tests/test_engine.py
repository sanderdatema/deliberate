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
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "quick")

        assert tracker.call_count == 5  # 3 analysts + 2 editors

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
        """AC-1: balanced = 5 analysts x 2 rounds + 4 editors = 14 total."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            await engine.run("Test question", "balanced")

        assert tracker.call_count == 14

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

        # Calls 6-10 are Round 2 (calls 1-5 are Round 1)
        round2_calls = tracker.calls[5:10]

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

        # Check a Round 2 call has the full 500-char output
        round2_call = tracker.calls[5]
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
        for call in tracker.calls[:3]:
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

        # Last 2 calls are editors (marx + samenvatter) in quick preset
        for call in tracker.calls[3:]:
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
                    name="test", description="", rounds=1,
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
                    name="test", description="", rounds=1,
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
                    name="test", description="", rounds=1,
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

    @pytest.mark.asyncio
    async def test_code_preset_has_no_summarizer(
        self, config: Config, personas: dict[str, Persona]
    ) -> None:
        """Code presets have no summarizer — code-synthesizer goes to editor_outputs."""
        tracker = make_mock_subprocess()
        with patch("deliberators.engine.asyncio.create_subprocess_exec", new=AsyncMock(side_effect=tracker)):
            engine = DeliberationEngine(config, personas)
            result = await engine.run("Review code", "code_quick")

        assert result.samenvatter_output is None
        assert "code-synthesizer" in result.editor_outputs


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
        first_system = tracker.get_system_prompt(0)
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

        assert tracker.call_count == 5


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
                    name="test", description="", rounds=1,
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
                    name="test", description="", rounds=1,
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
                    name="test", description="", rounds=1,
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

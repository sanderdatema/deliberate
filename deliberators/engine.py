"""Async orchestration engine for multi-agent deliberation."""

from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

from deliberators.loader import ConfigLoader, PersonaLoader
from deliberators.models import Config, DeliberationEvent, Persona, Preset

EventCallback = Callable[[DeliberationEvent], Awaitable[None] | None]
TextCallback = Callable[[str, str], Awaitable[None] | None]  # (agent_name, text_delta)
AgentFn = Callable[[Persona, str], Awaitable[str]]


@dataclass
class DeliberationResult:
    """Result of a complete deliberation run."""

    question: str
    preset: Preset
    rounds: dict[int, dict[str, str]] = field(default_factory=dict)
    editor_outputs: dict[str, str] = field(default_factory=dict)
    samenvatter_output: str | None = None
    code_context: str | None = None


class DeliberationEngine:
    """Orchestrates a multi-agent deliberation using claude -p subprocesses."""

    def __init__(
        self,
        config: Config,
        personas: dict[str, Persona],
        on_event: EventCallback | None = None,
        on_text: TextCallback | None = None,
        agent_fn: AgentFn | None = None,
    ) -> None:
        self.config = config
        self.personas = personas
        self.on_event = on_event
        self.on_text = on_text
        self._agent_fn = agent_fn

    async def run(
        self, question: str, preset_name: str | None = None,
        code_context: str | None = None,
    ) -> DeliberationResult:
        """Run a full deliberation and return the result."""
        preset_name = preset_name or self.config.default_preset
        preset = ConfigLoader.get_preset(self.config, preset_name)

        result = DeliberationResult(question=question, preset=preset, code_context=code_context)

        await self._emit(DeliberationEvent(type="deliberation_started", data={"preset": preset_name}))

        # Analyst rounds
        for round_num in range(1, preset.rounds + 1):
            prior_output = result.rounds.get(round_num - 1) if round_num > 1 else None
            round_output = await self._run_analyst_round(
                round_num, preset.analysts, question, prior_output, code_context
            )
            result.rounds[round_num] = round_output

        # Editorial round
        await self._emit(DeliberationEvent(type="editorial_started"))

        all_analyst_output = self._compile_analyst_output(result.rounds)
        prior_editor_output: dict[str, str] = {}

        for editor_name in preset.editors:
            if editor_name not in self.personas:
                logger.warning("Editor persona '%s' not found, skipping", editor_name)
                continue
            persona = self.personas[editor_name]

            await self._emit(DeliberationEvent(type="agent_started", agent_name=editor_name))

            prompt = self._build_editor_prompt(
                persona, question, all_analyst_output, prior_editor_output, code_context
            )
            output = await self._call_agent(persona, prompt)

            if editor_name == preset.summarizer:
                result.samenvatter_output = output
            else:
                result.editor_outputs[editor_name] = output
                prior_editor_output[editor_name] = output

            await self._emit(DeliberationEvent(
                type="agent_completed", agent_name=editor_name, data={"output": output}
            ))

        await self._emit(DeliberationEvent(type="editorial_completed"))
        await self._emit(DeliberationEvent(type="deliberation_completed"))

        return result

    async def _run_analyst_round(
        self,
        round_num: int,
        analyst_names: list[str],
        question: str,
        prior_round_output: dict[str, str] | None,
        code_context: str | None = None,
    ) -> dict[str, str]:
        """Run all analysts for a round in parallel with concurrency limit."""
        await self._emit(DeliberationEvent(type="round_started", round_number=round_num))

        sem = asyncio.Semaphore(self.config.max_concurrent)

        async def run_one(name: str) -> tuple[str, str]:
            async with sem:
                if name not in self.personas:
                    logger.warning("Persona '%s' not found, skipping", name)
                    return name, ""
                persona = self.personas[name]

                await self._emit(DeliberationEvent(
                    type="agent_started", agent_name=name, round_number=round_num
                ))

                prompt = self._build_analyst_prompt(
                    persona, question, round_num, prior_round_output, code_context
                )
                output = await self._call_agent(persona, prompt)

                await self._emit(DeliberationEvent(
                    type="agent_completed", agent_name=name, round_number=round_num,
                    data={"output": output},
                ))
                return name, output

        results = await asyncio.gather(*(run_one(name) for name in analyst_names))
        round_output = dict(results)

        await self._emit(DeliberationEvent(type="round_completed", round_number=round_num))
        return round_output

    async def _call_agent(self, persona: Persona, prompt: str) -> str:
        """Call an agent using either the injected function or default subprocess."""
        if self._agent_fn:
            output = await self._agent_fn(persona, prompt)
        else:
            output = await self._subprocess_call(persona, prompt)
        if self.on_text:
            await _maybe_await(self.on_text(persona.name, output))
        return output

    async def _subprocess_call(self, persona: Persona, prompt: str) -> str:
        """Default agent implementation: call claude -p subprocess with timeout."""
        model = persona.model or self.config.model
        try:
            proc = await asyncio.create_subprocess_exec(
                "claude", "-p",
                "--model", model,
                "--system-prompt", persona.system_prompt,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode()),
                timeout=self.config.timeout,
            )

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error("Agent '%s' failed (exit %d): %s", persona.name, proc.returncode, error_msg)
                return f"[Agent fout: {persona.name} — exit code {proc.returncode}]"

            return stdout.decode()
        except asyncio.TimeoutError:
            logger.error("Agent '%s' timed out after %ds", persona.name, self.config.timeout)
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            return f"[Agent fout: {persona.name} — timeout na {self.config.timeout}s]"
        except Exception as e:
            logger.error("Agent '%s' failed: %s", persona.name, e)
            return f"[Agent fout: {persona.name} — {type(e).__name__}: {e}]"

    def _build_analyst_prompt(
        self,
        persona: Persona,
        question: str,
        round_num: int,
        prior_round_output: dict[str, str] | None,
        code_context: str | None = None,
    ) -> str:
        """Build the prompt for an analyst agent."""
        parts = [
            f"QUESTION FOR DELIBERATION:\n{question}",
        ]

        if code_context:
            parts.append(f"\nCODE UNDER REVIEW:\n{code_context}")

        if round_num > 1 and prior_round_output:
            perspectives = "\n\n".join(
                f"### {name}\n{output}"
                for name, output in prior_round_output.items()
            )
            parts.append(
                f"\nTHIS IS ROUND {round_num}. You have seen what the other thinkers said "
                f"in Round {round_num - 1}. React to their perspectives while maintaining "
                f"your constraints. You may sharpen, challenge, or revise your position. "
                f"Specifically address the strongest point that contradicts your approach.\n\n"
                f"ROUND {round_num - 1} PERSPECTIVES:\n{perspectives}"
            )

        parts.append(
            "\nProvide your analysis following your role's output structure. "
            "Be thorough but focused.\n"
            "Stay strictly within your reasoning constraints — they are not suggestions, "
            "they are absolute rules.\n"
            "Respond in the same language as the question."
        )

        return "\n\n".join(parts)

    def _build_editor_prompt(
        self,
        persona: Persona,
        question: str,
        all_analyst_output: str,
        prior_editor_output: dict[str, str],
        code_context: str | None = None,
    ) -> str:
        """Build the prompt for an editor agent."""
        parts = [
            f"ORIGINAL QUESTION:\n{question}",
        ]

        if code_context:
            parts.append(f"\nCODE UNDER REVIEW:\n{code_context}")

        parts.append(f"\nANALYST PERSPECTIVES (ALL ROUNDS):\n{all_analyst_output}")

        if prior_editor_output:
            editor_text = "\n\n".join(
                f"### {name}\n{output}"
                for name, output in prior_editor_output.items()
            )
            parts.append(f"\nPRIOR EDITORIAL ANALYSIS:\n{editor_text}")

        parts.append(
            "\nRespond in the same language as the question."
        )

        return "\n\n".join(parts)

    def _compile_analyst_output(self, rounds: dict[int, dict[str, str]]) -> str:
        """Compile all analyst output from all rounds into a single document."""
        sections: list[str] = []
        for round_num in sorted(rounds.keys()):
            sections.append(f"## Round {round_num}")
            for name, output in rounds[round_num].items():
                sections.append(f"### {name}\n{output}")
        return "\n\n".join(sections)

    async def _emit(self, event: DeliberationEvent) -> None:
        """Emit an event to the callback if registered."""
        if self.on_event:
            await _maybe_await(self.on_event(event))


async def _maybe_await(result: Any) -> None:
    """Await a result if it's a coroutine, otherwise discard."""
    if inspect.isawaitable(result):
        await result

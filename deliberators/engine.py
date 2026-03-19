"""Async orchestration engine for multi-agent deliberation."""

from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

from deliberators.loader import ConfigLoader, PersonaLoader
from deliberators.models import Config, DeliberationEvent, Persona, Preset

MODEL_MAP = {
    "opus": "claude-opus-4-20250514",
    "sonnet": "claude-sonnet-4-5-20250929",
    "haiku": "claude-haiku-4-5-20251001",
}

EventCallback = Callable[[DeliberationEvent], Awaitable[None] | None]
TextCallback = Callable[[str, str], Awaitable[None] | None]  # (agent_name, text_delta)


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
    """Orchestrates a multi-agent deliberation using the Anthropic API."""

    def __init__(
        self,
        client: AsyncAnthropic,
        config: Config,
        personas: dict[str, Persona],
        on_event: EventCallback | None = None,
        on_text: TextCallback | None = None,
    ) -> None:
        self.client = client
        self.config = config
        self.personas = personas
        self.on_event = on_event
        self.on_text = on_text

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
        """Run all analysts for a round in parallel."""
        await self._emit(DeliberationEvent(type="round_started", round_number=round_num))

        async def run_one(name: str) -> tuple[str, str]:
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
        """Make a single API call to an agent, streaming the response."""
        model = MODEL_MAP.get(self.config.model, self.config.model)

        try:
            async with self.client.messages.stream(
                model=model,
                max_tokens=4096,
                system=persona.system_prompt,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                chunks: list[str] = []
                async for text in stream.text_stream:
                    chunks.append(text)
                    if self.on_text:
                        await _maybe_await(self.on_text(persona.name, text))
                return "".join(chunks)
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

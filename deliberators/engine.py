"""Async orchestration engine for multi-agent deliberation."""

from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

from deliberators.loader import ConfigLoader, PersonaLoader
from deliberators.models import Config, ConvergenceResult, DeliberationEvent, IntakeBrief, Persona, Preset

EventCallback = Callable[[DeliberationEvent], Awaitable[None] | None]
TextCallback = Callable[[str, str], Awaitable[None] | None]  # (agent_name, text_delta)
AgentFn = Callable[[Persona, str], Awaitable[str]]
ClarificationCallback = Callable[[str], Awaitable[str] | str]

_INTAKE_SYSTEM_PROMPT = """\
You are an intake analyst for a multi-perspective deliberation system.
Your job is to assess whether the question is clear enough for a team of expert \
thinkers to deliberate on productively.

Analyze the question for:
- Implicit assumptions that should be made explicit
- Missing context that would significantly change the analysis
- Key dimensions or trade-offs worth exploring
- Whether the question is specific enough to deliberate

Output EXACTLY this structure (no other text before or after):
IS_CLEAR: yes|no
CLARIFICATION_QUESTION: [one focused question if not clear, or "none" if clear]
BRIEF: [2-4 sentences: what the question is really asking, key assumptions, \
dimensions to explore. Write in the same language as the question.]
"""

_MAX_CLARIFICATION_ROUNDS = 3

_CONVERGENCE_SYSTEM_PROMPT = """\
You are a convergence analyst for a multi-perspective deliberation system.
After each analyst round, you evaluate whether continuing with another round \
would add significant value.

Analyze the round output for:
- Are new perspectives still emerging, or have positions solidified?
- Are there significant unresolved disagreements worth exploring further?
- Would another round likely produce genuinely new insights?
- Have the analysts already covered the key dimensions of the question?

Output EXACTLY this structure (no other text before or after):
CONTINUE: yes|no
REASON: [1-2 sentences explaining your assessment]
"""


@dataclass
class DeliberationResult:
    """Result of a complete deliberation run."""

    question: str
    preset: Preset
    rounds: dict[int, dict[str, str]] = field(default_factory=dict)
    editor_outputs: dict[str, str] = field(default_factory=dict)
    samenvatter_output: str | None = None
    code_context: str | None = None
    intake_brief: IntakeBrief | None = None


class DeliberationEngine:
    """Orchestrates a multi-agent deliberation using claude -p subprocesses."""

    def __init__(
        self,
        config: Config,
        personas: dict[str, Persona],
        on_event: EventCallback | None = None,
        on_text: TextCallback | None = None,
        agent_fn: AgentFn | None = None,
        on_clarify: ClarificationCallback | None = None,
    ) -> None:
        self.config = config
        self.personas = personas
        self.on_event = on_event
        self.on_text = on_text
        self._agent_fn = agent_fn
        self.on_clarify = on_clarify

    async def run(
        self, question: str, preset_name: str | None = None,
        code_context: str | None = None,
    ) -> DeliberationResult:
        """Run a full deliberation and return the result."""
        preset_name = preset_name or self.config.default_preset
        preset = ConfigLoader.get_preset(self.config, preset_name)

        result = DeliberationResult(question=question, preset=preset, code_context=code_context)

        await self._emit(DeliberationEvent(type="deliberation_started", data={"preset": preset_name}))

        # Intake phase (skip for code presets)
        intake_brief: IntakeBrief | None = None
        if not preset_name.startswith("code_"):
            intake_brief = await self._run_intake(question)
            result.intake_brief = intake_brief

        # Analyst rounds (adaptive: min_rounds guaranteed, then convergence check)
        round_num = 0
        while round_num < preset.max_rounds:
            round_num += 1
            prior_output = result.rounds.get(round_num - 1) if round_num > 1 else None
            round_output = await self._run_analyst_round(
                round_num, preset.analysts, question, prior_output,
                code_context, intake_brief,
            )
            result.rounds[round_num] = round_output

            # Convergence check: after min_rounds, before max_rounds
            if round_num >= preset.min_rounds and round_num < preset.max_rounds:
                convergence = await self._run_convergence_check(
                    round_num, round_output, intake_brief,
                )
                if not convergence.should_continue:
                    break

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
        intake_brief: IntakeBrief | None = None,
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
                    persona, question, round_num, prior_round_output,
                    code_context, intake_brief,
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

    async def _call_functional_agent(
        self, system_prompt: str, prompt: str, model: str,
    ) -> str:
        """Call a functional agent (no Persona) via subprocess."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "claude", "-p",
                "--model", model,
                "--system-prompt", system_prompt,
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
                logger.error("Functional agent failed (exit %d): %s", proc.returncode, error_msg)
                return ""

            return stdout.decode()
        except asyncio.TimeoutError:
            logger.error("Functional agent timed out after %ds", self.config.timeout)
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            return ""
        except Exception as e:
            logger.error("Functional agent failed: %s", e)
            return ""

    @staticmethod
    def _parse_intake_output(output: str) -> dict[str, str]:
        """Parse structured intake agent output into fields."""
        result = {"is_clear": "yes", "clarification_question": "none", "brief": ""}
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.upper().startswith("IS_CLEAR:"):
                value = stripped.split(":", 1)[1].strip().lower()
                result["is_clear"] = "yes" if value.startswith("yes") else "no"
            elif stripped.upper().startswith("CLARIFICATION_QUESTION:"):
                result["clarification_question"] = stripped.split(":", 1)[1].strip()
            elif stripped.upper().startswith("BRIEF:"):
                result["brief"] = stripped.split(":", 1)[1].strip()
        # Fallback: if brief is empty, use first 500 chars of output
        if not result["brief"] and output.strip():
            result["brief"] = output.strip()[:500]
        return result

    async def _run_intake(self, question: str) -> IntakeBrief:
        """Run the intake phase: analyze question clarity, optionally clarify."""
        await self._emit(DeliberationEvent(type="intake_started"))

        clarifications: list[tuple[str, str]] = []
        current_prompt = f"QUESTION:\n{question}"
        parsed: dict[str, str] = {"is_clear": "yes", "brief": question, "clarification_question": "none"}

        for iteration in range(_MAX_CLARIFICATION_ROUNDS):
            output = await self._call_functional_agent(
                _INTAKE_SYSTEM_PROMPT, current_prompt, self.config.model,
            )
            parsed = self._parse_intake_output(output)

            is_clear = parsed["is_clear"] == "yes"
            clarification_q = parsed.get("clarification_question", "none")

            if is_clear or not self.on_clarify or clarification_q.lower() == "none":
                break

            # Ask user for clarification
            user_answer = self.on_clarify(clarification_q)
            if inspect.isawaitable(user_answer):
                user_answer = await user_answer

            if not user_answer:
                break

            clarifications.append((clarification_q, user_answer))

            # Rebuild prompt with accumulated context
            context_lines = "\n".join(
                f"Q: {q}\nA: {a}" for q, a in clarifications
            )
            current_prompt = (
                f"QUESTION:\n{question}\n\n"
                f"ADDITIONAL CONTEXT FROM USER:\n{context_lines}"
            )

        brief = IntakeBrief(
            question=question,
            summary=parsed.get("brief", ""),
            clarifications=tuple(clarifications),
            is_clear=parsed["is_clear"] == "yes",
        )

        await self._emit(DeliberationEvent(
            type="intake_completed",
            data={"is_clear": brief.is_clear, "had_clarifications": len(clarifications) > 0},
        ))

        return brief

    @staticmethod
    def _parse_convergence_output(output: str) -> dict[str, str]:
        """Parse structured convergence agent output into fields."""
        result = {"continue": "yes", "reason": ""}
        for line in output.splitlines():
            stripped = line.strip()
            if stripped.upper().startswith("CONTINUE:"):
                value = stripped.split(":", 1)[1].strip().lower()
                result["continue"] = "yes" if value.startswith("yes") else "no"
            elif stripped.upper().startswith("REASON:"):
                result["reason"] = stripped.split(":", 1)[1].strip()
        if not result["reason"] and output.strip():
            result["reason"] = output.strip()[:200]
        return result

    async def _run_convergence_check(
        self,
        round_num: int,
        round_output: dict[str, str],
        intake_brief: IntakeBrief | None = None,
    ) -> ConvergenceResult:
        """Check whether another analyst round would add value."""
        await self._emit(DeliberationEvent(type="convergence_started", round_number=round_num))

        perspectives = "\n\n".join(
            f"### {name}\n{output}" for name, output in round_output.items()
        )
        prompt_parts = []
        if intake_brief and intake_brief.summary:
            prompt_parts.append(f"QUESTION CONTEXT:\n{intake_brief.summary}")
        prompt_parts.append(f"ROUND {round_num} OUTPUT:\n{perspectives}")
        prompt_parts.append(
            f"Should the deliberation continue to Round {round_num + 1}?"
        )
        prompt = "\n\n".join(prompt_parts)

        output = await self._call_functional_agent(
            _CONVERGENCE_SYSTEM_PROMPT, prompt, self.config.model,
        )
        parsed = self._parse_convergence_output(output)

        should_continue = parsed["continue"] == "yes"
        reason = parsed.get("reason", "")

        convergence = ConvergenceResult(
            should_continue=should_continue,
            reason=reason,
            round_number=round_num,
        )

        await self._emit(DeliberationEvent(
            type="convergence_completed",
            round_number=round_num,
            data={"should_continue": should_continue, "reason": reason},
        ))

        return convergence

    def _build_analyst_prompt(
        self,
        persona: Persona,
        question: str,
        round_num: int,
        prior_round_output: dict[str, str] | None,
        code_context: str | None = None,
        intake_brief: IntakeBrief | None = None,
    ) -> str:
        """Build the prompt for an analyst agent."""
        parts: list[str] = []

        if intake_brief and intake_brief.summary:
            parts.append(f"INTAKE CONTEXT:\n{intake_brief.summary}")

        parts.append(f"QUESTION FOR DELIBERATION:\n{question}")

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

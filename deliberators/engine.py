"""Async orchestration engine for multi-agent deliberation."""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)

from deliberators.loader import ConfigLoader
from deliberators.models import (
    Config, ConvergenceResult, DecisionRecord, DeliberationEvent, DeliberationResult,
    IntakeBrief, Persona, Preset,
)
from deliberators.prompts import (
    build_analyst_prompt,
    build_convergence_prompt,
    build_editor_prompt,
    build_synthesis_prompt,
    build_team_selection_prompt,
    compile_analyst_output,
)

EventCallback = Callable[[DeliberationEvent], Awaitable[None] | None]
TextCallback = Callable[[str, str], Awaitable[None] | None]  # (agent_name, text_delta)
AgentFn = Callable[[Persona, str], Awaitable[str]]
ClarificationCallback = Callable[[str], Awaitable[str] | str]
# (analysts, editors, reason, motivations) → approved (analysts, editors) or None to abort
TeamApprovalCallback = Callable[
    [list[str], list[str], str, dict[str, str]],
    Awaitable[tuple[list[str], list[str]] | None] | tuple[list[str], list[str]] | None,
]

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

_TEAM_SELECTION_SYSTEM_PROMPT = """\
You are a team selection agent for a multi-perspective deliberation system.
Your job is to select the optimal team of analysts and editors from a pool of \
expert personas to deliberate on the given question.

Select personas whose expertise domains are most relevant to the question.
Ensure diversity of perspective — avoid selecting personas with highly overlapping domains.

GENDER BALANCE: Select a team with at least 40% representation of each binary \
gender (M/F) when the pool allows. Include non-binary personas where relevant.

Output EXACTLY this structure (no other text before or after):
ANALYSTS: name1, name2, name3
EDITORS: name1, name2
REASON: [1-2 sentences explaining your selection rationale]
MOTIVATIONS: name1: why this persona fits | name2: why this persona fits | ...
"""

_SYNTHESIS_SYSTEM_PROMPT = """\
You are a synthesis agent for a multi-perspective deliberation system.
You receive the complete output from all analyst rounds and editorial analyses.
Your job is to synthesize this into a thematic report that organizes insights \
by topic, not by who said what.

Write EXACTLY these sections with these headers (no other text before or after).

CRITICAL: Be concise. This is an executive summary, not a transcript.
- Each section: maximum 3-4 short paragraphs or a bullet list
- Use bullet points instead of long prose paragraphs
- Actiepunten: maximum 5 items, each 1-2 sentences
- Total output: aim for 400-600 words, never exceed 800 words
- No filler phrases, no repetition of what analysts said verbatim

## Het Landschap
What is this question really about? Key dimensions, stakeholders, forces at play. \
Synthesize into a coherent picture — do not list what each analyst said separately.

## Spanningsvelden
Where do analysts fundamentally disagree? Present each tension as X vs Y \
with the strongest argument on each side. Maximum 3-4 tensions.

## Blinde Vlekken
What did nobody question? Shared assumptions. \
Draw primarily from editorial analyses. Keep to 2-3 key blind spots.

## Verschuiving
How did positions evolve between rounds? Who changed their mind and why? \
Skip this section entirely if there was only 1 round.

## Actiepunten
3-5 concrete, actionable next steps. Each specific enough to act on tomorrow. \
Prioritize by impact and feasibility. One line per action.

Write in the same language as the original question.
"""

_CONVERGENCE_SYSTEM_PROMPT = """\
You are a convergence analyst for a multi-perspective deliberation system.
After each analyst round, you evaluate whether the deliberation has reached \
sufficient depth of interaction.

Key principle: the value of multiple rounds lies in cross-pollination — analysts \
challenging, building on, and responding to each other's arguments. Positions that \
stand side-by-side without mutual engagement have not yet been tested.

Evaluate based on:
- Have analysts engaged with and responded to each other's specific arguments? \
(If not, another round adds value.)
- Are there unresolved tensions, contradictions, or blind spots between perspectives?
- Have positions been refined through mutual challenge, or do they merely coexist?
- Would another round deepen the analysis through genuine dialogue, or would it \
repeat established positions?

Err on the side of continuing when perspectives haven't sufficiently interacted.

Output EXACTLY this structure (no other text before or after):
CONTINUE: yes|no
REASON: [1-2 sentences explaining your assessment]
"""


def _parse_kv_lines(
    output: str, fields: dict[str, str], context: str,
) -> tuple[dict[str, str], bool]:
    """Parse KEY: value lines from structured LLM output.

    Args:
        output: Raw text output to parse.
        fields: Mapping of UPPERCASE prefix → result key (e.g. {"IS_CLEAR": "is_clear"}).
        context: Name for log messages (e.g. "Intake").

    Returns:
        (parsed_values, parsed_any) — values dict keyed by result keys, and
        whether any field was successfully parsed.
    """
    result: dict[str, str] = {}
    parsed_any = False
    for line in output.splitlines():
        stripped = line.strip()
        upper = stripped.upper()
        for prefix, key in fields.items():
            if upper.startswith(prefix + ":"):
                result[key] = stripped.split(":", 1)[1].strip()
                parsed_any = True
                break
    if not parsed_any:
        logger.warning("%s: no fields parsed from output: %.200s", context, output)
    return result, parsed_any


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
        on_approve_team: TeamApprovalCallback | None = None,
    ) -> None:
        self.config = config
        self.personas = personas
        self.on_event = on_event
        self.on_text = on_text
        self._agent_fn = agent_fn
        self.on_clarify = on_clarify
        self.on_approve_team = on_approve_team

    async def run(
        self, question: str, preset_name: str | None = None,
        code_context: str | None = None,
        prior_decision: DecisionRecord | None = None,
    ) -> DeliberationResult:
        """Run a full deliberation and return the result."""
        preset_name = preset_name or self.config.default_preset
        preset = ConfigLoader.get_preset(self.config, preset_name)

        result = DeliberationResult(question=question, preset=preset, code_context=code_context)

        await self._emit(DeliberationEvent(type="deliberation_started", data={"preset": preset_name}))

        # Intake phase (always runs)
        intake_brief = await self._run_intake(question)
        result.intake_brief = intake_brief

        # Team selection: use fixed lists if preset has them, otherwise dynamic selection
        if preset.analysts and preset.editors:
            analyst_names = list(preset.analysts)
            editor_names = list(preset.editors)
        else:
            analyst_names, editor_names = await self._run_team_selection(
                question, preset, intake_brief, code_context,
            )

        # Analyst rounds (adaptive: min_rounds guaranteed, then convergence check)
        round_num = 0
        while round_num < preset.max_rounds:
            round_num += 1
            prior_output = result.rounds.get(round_num - 1) if round_num > 1 else None
            round_output = await self._run_analyst_round(
                round_num, analyst_names, question, prior_output,
                code_context, intake_brief, prior_decision,
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

        all_analyst_output = compile_analyst_output(result.rounds)
        prior_editor_output: dict[str, str] = {}

        for editor_name in editor_names:
            if editor_name not in self.personas:
                logger.warning("Editor persona '%s' not found, skipping", editor_name)
                continue
            persona = self.personas[editor_name]

            await self._emit(DeliberationEvent(type="agent_started", agent_name=editor_name))

            prompt = build_editor_prompt(
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

        # Synthesis: generate thematic report sections
        synthesis = await self._run_synthesis(
            question, all_analyst_output, result.editor_outputs,
            result.samenvatter_output, len(result.rounds),
        )
        if synthesis:
            result.synthesis_output = synthesis

        await self._emit(DeliberationEvent(type="deliberation_completed"))

        return result

    async def _run_analyst_round(
        self,
        round_num: int,
        analyst_names: list[str] | tuple[str, ...],
        question: str,
        prior_round_output: dict[str, str] | None,
        code_context: str | None = None,
        intake_brief: IntakeBrief | None = None,
        prior_decision: DecisionRecord | None = None,
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

                prompt = build_analyst_prompt(
                    persona, question, round_num, prior_round_output,
                    code_context, intake_brief, prior_decision,
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
            output = await self._subprocess_call(
                persona.system_prompt, prompt,
                persona.model or self.config.model, persona.name,
            )
        if self.on_text:
            await _maybe_await(self.on_text(persona.name, output))
        return output

    async def _subprocess_call(
        self, system_prompt: str, prompt: str, model: str, name: str = "functional",
    ) -> str:
        """Call claude -p subprocess with timeout. Used by both persona and functional agents."""
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
                logger.error("Agent '%s' failed (exit %d): %s", name, proc.returncode, error_msg)
                return f"[Agent fout: {name} — exit code {proc.returncode}]"

            return stdout.decode()
        except asyncio.TimeoutError:
            logger.error("Agent '%s' timed out after %ds", name, self.config.timeout)
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            return f"[Agent fout: {name} — timeout na {self.config.timeout}s]"
        except Exception as e:
            logger.error("Agent '%s' failed: %s", name, e)
            return f"[Agent fout: {name} — {type(e).__name__}: {e}]"

    @staticmethod
    def _parse_intake_output(output: str) -> dict[str, str]:
        """Parse structured intake agent output into fields."""
        fields = {
            "IS_CLEAR": "is_clear",
            "CLARIFICATION_QUESTION": "clarification_question",
            "BRIEF": "brief",
        }
        parsed, _ = _parse_kv_lines(output, fields, "Intake")
        # Normalize is_clear to yes/no
        raw_clear = parsed.get("is_clear", "").lower()
        result: dict[str, str] = {
            "is_clear": "yes" if not raw_clear or raw_clear.startswith("yes") else "no",
            "clarification_question": parsed.get("clarification_question", "none"),
            "brief": parsed.get("brief", ""),
        }
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

        for _ in range(_MAX_CLARIFICATION_ROUNDS):
            output = await self._subprocess_call(
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
    def _parse_team_selection_output(
        output: str, available_personas: dict[str, Persona],
        expected_analysts: int = 0, expected_editors: int = 0,
    ) -> tuple[list[str], list[str], str, dict[str, str]]:
        """Parse team selection output into (analysts, editors, reason, motivations)."""
        fields = {
            "ANALYSTS": "analysts", "EDITORS": "editors",
            "REASON": "reason", "MOTIVATIONS": "motivations",
        }
        parsed, _ = _parse_kv_lines(output, fields, "Team selection")

        # Split comma-separated name lists
        raw_analysts = parsed.get("analysts", "")
        raw_editors = parsed.get("editors", "")
        analysts = [n.strip() for n in raw_analysts.split(",") if n.strip()]
        editors = [n.strip() for n in raw_editors.split(",") if n.strip()]
        reason = parsed.get("reason", "")

        # Parse motivations: "name1: why | name2: why | ..."
        motivations: dict[str, str] = {}
        raw_motivations = parsed.get("motivations", "")
        if raw_motivations:
            for entry in raw_motivations.split("|"):
                entry = entry.strip()
                if ":" in entry:
                    name, motivation = entry.split(":", 1)
                    motivations[name.strip()] = motivation.strip()

        # Validate: only keep names that exist in personas
        valid_analysts = [n for n in analysts if n in available_personas and available_personas[n].role == "analyst"]
        valid_editors = [n for n in editors if n in available_personas and available_personas[n].role == "editor"]

        if expected_analysts and len(valid_analysts) != expected_analysts:
            logger.warning(
                "Team selection: expected %d analysts, got %d",
                expected_analysts, len(valid_analysts),
            )
        if expected_editors and len(valid_editors) != expected_editors:
            logger.warning(
                "Team selection: expected %d editors, got %d",
                expected_editors, len(valid_editors),
            )

        return valid_analysts, valid_editors, reason, motivations

    async def _run_team_selection(
        self,
        question: str,
        preset: Preset,
        intake_brief: IntakeBrief | None = None,
        code_context: str | None = None,
    ) -> tuple[list[str], list[str]]:
        """Select analysts and editors from the pool using a functional agent."""
        prompt = build_team_selection_prompt(
            self.personas, question, preset, intake_brief, code_context,
        )

        output = await self._subprocess_call(
            _TEAM_SELECTION_SYSTEM_PROMPT, prompt, self.config.model,
        )

        analysts, editors, reason, motivations = self._parse_team_selection_output(
            output, self.personas,
            expected_analysts=preset.team_size, expected_editors=preset.editor_count,
        )

        # Fallback: if selection is empty or insufficient, use preset overrides
        if not analysts or not editors:
            if preset.analysts and preset.editors:
                logger.warning("Team selection failed, falling back to preset fixed lists")
                return list(preset.analysts), list(preset.editors)
            # Last resort: pick first N analysts and editors from pool
            logger.warning("Team selection failed with no preset fallback, picking from pool")
            all_analysts = [k for k, p in self.personas.items() if p.role == "analyst"]
            all_editors = [k for k, p in self.personas.items() if p.role == "editor"]
            return all_analysts[:preset.team_size], all_editors[:preset.editor_count]

        await self._emit(DeliberationEvent(
            type="team_selected",
            data={
                "analysts": analysts,
                "editors": editors,
                "reason": reason,
                "motivations": motivations,
            },
        ))

        # Ask user for team approval if callback is registered
        if self.on_approve_team:
            approval = self.on_approve_team(analysts, editors, reason, motivations)
            if inspect.isawaitable(approval):
                approval = await approval
            if approval is None:
                logger.info("Team approval: user aborted deliberation")
                raise SystemExit(0)
            analysts, editors = approval

        return analysts, editors

    @staticmethod
    def _parse_convergence_output(output: str) -> dict[str, str]:
        """Parse structured convergence agent output into fields."""
        fields = {"CONTINUE": "continue", "REASON": "reason"}
        parsed, _ = _parse_kv_lines(output, fields, "Convergence")
        # Normalize continue to yes/no
        raw_cont = parsed.get("continue", "").lower()
        result: dict[str, str] = {
            "continue": "yes" if not raw_cont or raw_cont.startswith("yes") else "no",
            "reason": parsed.get("reason", ""),
        }
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

        prompt = build_convergence_prompt(round_num, round_output, intake_brief)

        output = await self._subprocess_call(
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

    async def _run_synthesis(
        self,
        question: str,
        all_analyst_output: str,
        editor_output: dict[str, str],
        samenvatter_output: str | None,
        num_rounds: int,
    ) -> str:
        """Run synthesis agent to generate thematic report sections."""
        prompt = build_synthesis_prompt(
            question, all_analyst_output, editor_output, samenvatter_output, num_rounds,
        )
        output = await self._subprocess_call(
            _SYNTHESIS_SYSTEM_PROMPT, prompt, self.config.model,
        )
        return output

    async def _emit(self, event: DeliberationEvent) -> None:
        """Emit an event to the callback if registered."""
        if self.on_event:
            await _maybe_await(self.on_event(event))


async def _maybe_await(result: object) -> None:
    """Await a result if it's a coroutine, otherwise discard."""
    if inspect.isawaitable(result):
        await result

"""Prompt builders for analyst, editor, and team selection agents.

All functions are pure: they transform data into prompt strings without
touching the engine's subprocess or callback machinery.
"""

from __future__ import annotations

from deliberators.models import DecisionRecord, IntakeBrief, Persona


def build_persona_catalog(personas: dict[str, Persona]) -> str:
    """Build a catalog of all personas for the team selection agent."""
    lines = []
    for key, persona in sorted(personas.items()):
        domains = ", ".join(persona.domains)
        lines.append(f"- {key} | role={persona.role} | domains={domains}")
    return "\n".join(lines)


def build_analyst_prompt(
    persona: Persona,
    question: str,
    round_num: int,
    prior_round_output: dict[str, str] | None,
    code_context: str | None = None,
    intake_brief: IntakeBrief | None = None,
    prior_decision: DecisionRecord | None = None,
) -> str:
    """Build the prompt for an analyst agent."""
    parts: list[str] = []

    if prior_decision:
        positions_text = "\n".join(
            f"- {name}: {pos}" for name, pos in prior_decision.key_positions.items()
        )
        parts.append(
            f"PRIOR DELIBERATION CONTEXT:\n"
            f"Question: {prior_decision.question}\n"
            f"Conclusion: {prior_decision.summary}\n"
            f"Key positions:\n{positions_text}"
        )

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


def build_editor_prompt(
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


def compile_analyst_output(rounds: dict[int, dict[str, str]]) -> str:
    """Compile all analyst output from all rounds into a single document."""
    sections: list[str] = []
    for round_num in sorted(rounds.keys()):
        sections.append(f"## Round {round_num}")
        for name, output in rounds[round_num].items():
            sections.append(f"### {name}\n{output}")
    return "\n\n".join(sections)

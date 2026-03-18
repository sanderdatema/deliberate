"""Format DeliberationResult as markdown."""

from __future__ import annotations

from deliberators.engine import DeliberationResult
from deliberators.models import Persona


class ResultFormatter:
    """Formats a DeliberationResult as readable markdown."""

    def __init__(self, personas: dict[str, Persona]) -> None:
        self.personas = personas

    def format(self, result: DeliberationResult) -> str:
        """Format the full deliberation result as markdown."""
        sections: list[str] = []

        # Samenvatter first (Kort & Concreet)
        if result.samenvatter_output:
            sections.append("## Kort & Concreet\n")
            sections.append(result.samenvatter_output)
            sections.append("\n---\n")

        # Title
        sections.append(f"# Deliberatie: {result.question}\n")

        # Analyst rounds
        for round_num in sorted(result.rounds.keys()):
            round_label = "Onafhankelijke Analyse" if round_num == 1 else "Reactieve Deliberatie"
            sections.append(f"## Ronde {round_num}: {round_label}\n")

            for name, output in result.rounds[round_num].items():
                persona = self.personas.get(name)
                style = f" — {persona.reasoning_style}" if persona else ""
                label = "Reactie" if round_num > 1 else persona.reasoning_style if persona else ""
                header = f"{persona.name}{' — ' + label if label else ''}" if persona else name
                sections.append(f"### {header}\n{output}\n")

        # Editorial round
        if result.editor_outputs:
            sections.append("---\n")
            sections.append("## Redactionele Analyse\n")
            for name, output in result.editor_outputs.items():
                persona = self.personas.get(name)
                style = f" — {persona.reasoning_style}" if persona else ""
                header = f"{persona.name}{style}" if persona else name
                sections.append(f"### {header}\n{output}\n")

        # Samenvatter in full report position too
        if result.samenvatter_output:
            sections.append("---\n")

        return "\n".join(sections)

"""Format DeliberationResult as markdown."""

from __future__ import annotations

from deliberators.engine import DeliberationResult
from deliberators.models import Persona


class ResultFormatter:
    """Formats a DeliberationResult as readable markdown."""

    def __init__(self, personas: dict[str, Persona]) -> None:
        self.personas = personas

    def format(self, result: DeliberationResult) -> str:
        """Format the full deliberation result as markdown.

        If synthesis_output is available, produces a thematic report.
        Otherwise, falls back to per-persona format.
        """
        if result.synthesis_output:
            return self._format_thematic(result)
        return self._format_per_persona(result)

    def _format_thematic(self, result: DeliberationResult) -> str:
        """Thematic report: synthesis sections + per-persona appendix."""
        sections: list[str] = []

        # Samenvatter first (Kort & Concreet)
        if result.samenvatter_output:
            sections.append("## Kort & Concreet\n")
            sections.append(result.samenvatter_output)
            sections.append("\n---\n")

        # Title
        sections.append(f"# Deliberatie: {result.question}\n")

        # Synthesis sections (already contain ## headers)
        sections.append(result.synthesis_output)

        # Appendix: per-persona output
        sections.append("\n---\n")
        sections.append("## Volledig Verslag\n")
        sections.append(self._render_per_persona_body(result))

        return "\n".join(sections)

    def _format_per_persona(self, result: DeliberationResult) -> str:
        """Legacy per-persona format (fallback when no synthesis)."""
        sections: list[str] = []

        # Samenvatter first (Kort & Concreet)
        if result.samenvatter_output:
            sections.append("## Kort & Concreet\n")
            sections.append(result.samenvatter_output)
            sections.append("\n---\n")

        # Title
        sections.append(f"# Deliberatie: {result.question}\n")

        # Per-persona body
        sections.append(self._render_per_persona_body(result))

        return "\n".join(sections)

    def _render_per_persona_body(self, result: DeliberationResult) -> str:
        """Render all analyst rounds + editor output as per-persona sections."""
        sections: list[str] = []

        # Analyst rounds
        for round_num in sorted(result.rounds.keys()):
            round_label = "Onafhankelijke Analyse" if round_num == 1 else "Reactieve Deliberatie"
            sections.append(f"### Ronde {round_num}: {round_label}\n")

            for name, output in result.rounds[round_num].items():
                persona = self.personas.get(name)
                label = "Reactie" if round_num > 1 else persona.reasoning_style if persona else ""
                header = f"{persona.name}{' — ' + label if label else ''}" if persona else name
                sections.append(f"#### {header}\n{output}\n")

        # Editorial round
        if result.editor_outputs:
            sections.append("### Redactionele Analyse\n")
            for name, output in result.editor_outputs.items():
                persona = self.personas.get(name)
                style = f" — {persona.reasoning_style}" if persona else ""
                header = f"{persona.name}{style}" if persona else name
                sections.append(f"#### {header}\n{output}\n")

        return "\n".join(sections)

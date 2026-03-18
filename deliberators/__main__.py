"""CLI entry point: python -m deliberators "question" --preset quick."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from anthropic import AsyncAnthropic

from deliberators.engine import DeliberationEngine
from deliberators.formatter import ResultFormatter
from deliberators.loader import ConfigLoader, PersonaLoader
from deliberators.models import DeliberationEvent


def _print_event(event: DeliberationEvent) -> None:
    """Print progress events to stderr."""
    match event.type:
        case "deliberation_started":
            preset = event.data.get("preset", "?")
            print(f"Deliberatie gestart (preset: {preset})", file=sys.stderr)
        case "round_started":
            print(f"  Ronde {event.round_number} gestart...", file=sys.stderr)
        case "agent_started":
            rnd = f" (R{event.round_number})" if event.round_number else ""
            print(f"    → {event.agent_name}{rnd}", file=sys.stderr)
        case "agent_completed":
            rnd = f" (R{event.round_number})" if event.round_number else ""
            print(f"    ✓ {event.agent_name}{rnd}", file=sys.stderr)
        case "round_completed":
            print(f"  Ronde {event.round_number} compleet", file=sys.stderr)
        case "editorial_started":
            print("  Redactionele fase...", file=sys.stderr)
        case "editorial_completed":
            print("  Redactie compleet", file=sys.stderr)
        case "deliberation_completed":
            print("Deliberatie afgerond.", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="deliberators",
        description="Multi-perspectief AI deliberatie engine",
    )
    parser.add_argument(
        "question",
        help="De vraag om over te delibereren",
    )
    parser.add_argument(
        "--preset",
        choices=["quick", "balanced", "deep"],
        default=None,
        help="Preset te gebruiken (default: uit config.yaml)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Pad naar config.yaml (default: config.yaml)",
    )
    parser.add_argument(
        "--personas-dir",
        type=Path,
        default=Path("personas"),
        help="Pad naar personas directory (default: personas)",
    )
    return parser


async def _run(args: argparse.Namespace) -> int:
    """Run the deliberation and return exit code."""
    config = ConfigLoader.load(args.config)
    personas = PersonaLoader.load_all(args.personas_dir)
    custom = PersonaLoader.discover_custom(args.personas_dir)
    for p in custom:
        personas[p.name.lower().replace(" ", "-")] = p

    client = AsyncAnthropic()
    engine = DeliberationEngine(
        client=client,
        config=config,
        personas=personas,
        on_event=_print_event,
    )

    result = await engine.run(args.question, args.preset)

    formatter = ResultFormatter(personas)
    print(formatter.format(result))
    return 0


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        exit_code = asyncio.run(_run(args))
    except KeyboardInterrupt:
        print("\nAfgebroken.", file=sys.stderr)
        exit_code = 130
    except Exception as e:
        print(f"Fout: {e}", file=sys.stderr)
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

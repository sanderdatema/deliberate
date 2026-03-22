"""CLI entry point: python -m deliberators "question" --preset quick."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from deliberators.context import build_code_context
from deliberators.engine import DeliberationEngine
from deliberators.formatter import ResultFormatter
from deliberators.loader import ConfigLoader, PersonaLoader, resolve_config_path, resolve_personas_dir
from deliberators.models import DeliberationEvent
from deliberators.web_pusher import WebPusher


def _print_event(event: DeliberationEvent) -> None:
    """Print progress events to stderr."""
    match event.type:
        case "deliberation_started":
            preset = event.data.get("preset", "?")
            print(f"Deliberatie gestart (preset: {preset})", file=sys.stderr)
        case "intake_started":
            print("  Intake analyse...", file=sys.stderr)
        case "intake_completed":
            status = "helder" if event.data.get("is_clear") else "verduidelijkt"
            print(f"  Intake {status}", file=sys.stderr)
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
        case "convergence_started":
            print(f"  Convergentie check...", file=sys.stderr)
        case "convergence_completed":
            action = "doorgaan" if event.data.get("should_continue") else "stoppen"
            reason = event.data.get("reason", "")
            print(f"  Convergentie: {action}" + (f" — {reason}" if reason else ""), file=sys.stderr)
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
        choices=["quick", "balanced", "deep", "code_quick", "code_balanced", "code_deep"],
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
    parser.add_argument(
        "--files",
        nargs="+",
        type=Path,
        default=None,
        help="Code files to include as context for code review",
    )
    parser.add_argument(
        "--web",
        type=str,
        default=None,
        metavar="URL",
        help="Push events to web viewer (e.g., http://localhost:8000)",
    )
    return parser


async def _run(args: argparse.Namespace) -> int:
    """Run the deliberation and return exit code."""
    config_path = resolve_config_path(args.config)
    personas_dir = resolve_personas_dir(args.personas_dir)
    config = ConfigLoader.load(config_path)
    personas = PersonaLoader.load_all(personas_dir)

    ConfigLoader.validate_preset_personas(config, personas)

    # Set up web pusher if --web is specified
    web: WebPusher | None = None
    if args.web:
        web = WebPusher(args.web)
        session_id = await web.create_session()
        print(
            f"Web viewer: {args.web} (sessie: {session_id})",
            file=sys.stderr,
        )
        print(
            f"Open {args.web} in je browser en verbind met sessie {session_id}",
            file=sys.stderr,
        )

    async def on_event(event: DeliberationEvent) -> None:
        _print_event(event)
        if web:
            await web.push_event(event)

    async def on_text(agent_name: str, text: str) -> None:
        if web:
            await web.push_text(agent_name, text)

    async def on_clarify(question: str) -> str:
        if sys.stdin.isatty():
            print(f"\n  Intake vraag: {question}", file=sys.stderr)
            return input("  Jouw antwoord: ")
        return ""

    engine = DeliberationEngine(
        config=config,
        personas=personas,
        on_event=on_event,
        on_text=on_text if web else None,
        on_clarify=on_clarify,
    )

    code_context = None
    if args.files:
        code_context = build_code_context(args.files)

    result = await engine.run(args.question, args.preset, code_context=code_context)

    formatter = ResultFormatter(personas)
    formatted = formatter.format(result)

    if web:
        await web.push_result(formatted)
        await web.close()

    print(formatted)
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

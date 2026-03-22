"""CLI entry point: python -m deliberators "question" --preset quick."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from deliberators.context import build_code_context
from deliberators.engine import DeliberationEngine, to_decision_record
from deliberators.formatter import ResultFormatter
from deliberators.loader import ConfigLoader, PersonaLoader, resolve_config_path, resolve_personas_dir
from deliberators.models import DeliberationEvent
from deliberators.storage import DecisionStore
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
        case "team_selected":
            analysts = event.data.get("analysts", [])
            editors = event.data.get("editors", [])
            print(f"  Team samengesteld: {len(analysts)} analisten, {len(editors)} editors", file=sys.stderr)
            print(f"    Analisten: {', '.join(analysts)}", file=sys.stderr)
            print(f"    Editors: {', '.join(editors)}", file=sys.stderr)
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
        nargs="?",
        default=None,
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
    parser.add_argument(
        "--history",
        action="store_true",
        default=False,
        help="Toon recente deliberaties",
    )
    parser.add_argument(
        "--followup",
        type=str,
        default=None,
        metavar="ID",
        help="Vervolg op een eerdere deliberatie (ID of prefix)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Toon volledig verslag (per-persona output) in rapport",
    )
    return parser


def _print_history() -> int:
    """Print recent deliberations and return exit code."""
    store = DecisionStore()
    records = store.list_recent()
    if not records:
        print("Geen eerdere deliberaties gevonden.", file=sys.stderr)
        return 0
    print(f"{'Datum':<22} {'ID':<10} {'Preset':<10} {'Vraag'}")
    print("-" * 80)
    for r in records:
        date = r.timestamp[:19].replace("T", " ")
        short_id = r.id[:8]
        question = r.question[:40] + ("..." if len(r.question) > 40 else "")
        print(f"{date:<22} {short_id:<10} {r.preset_name:<10} {question}")
    return 0


async def _run(args: argparse.Namespace) -> int:
    """Run the deliberation and return exit code."""
    config_path = resolve_config_path(args.config)
    personas_dir = resolve_personas_dir(args.personas_dir)
    config = ConfigLoader.load(config_path)
    personas = PersonaLoader.load_all(personas_dir)

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

    # Load prior decision for follow-up
    prior_decision = None
    if args.followup:
        store = DecisionStore()
        prior_decision = store.load(args.followup)
        if prior_decision is None:
            print(f"Besluit '{args.followup}' niet gevonden.", file=sys.stderr)
            return 1
        print(f"Vervolg op: {prior_decision.question[:60]}", file=sys.stderr)

    try:
        result = await engine.run(
            args.question, args.preset, code_context=code_context,
            prior_decision=prior_decision,
        )

        formatter = ResultFormatter(personas)
        formatted = formatter.format(result, verbose=args.verbose)

        # Save decision record
        follow_up_of = prior_decision.id if prior_decision else None
        record = to_decision_record(result, follow_up_of=follow_up_of)
        store = DecisionStore()
        store.save(record)
        print(f"Besluit opgeslagen: {record.id[:8]}", file=sys.stderr)

        if web:
            await web.push_result(formatted)

        print(formatted)
        return 0
    finally:
        if web:
            await web.close()


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.history:
        sys.exit(_print_history())

    if not args.question:
        parser.error("question is required (unless using --history)")

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

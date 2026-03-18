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


class WebPusher:
    """Push events to the web viewer server via HTTP."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session_id: str | None = None

    async def create_session(self) -> str:
        """Create a viewer session and return the session ID."""
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/api/session")
            resp.raise_for_status()
            data = resp.json()
            self.session_id = data["id"]
            return self.session_id

    async def push_event(self, event: DeliberationEvent) -> None:
        """Push a DeliberationEvent to the viewer."""
        if not self.session_id:
            return
        import httpx

        payload = {
            "type": event.type,
            "agent_name": event.agent_name,
            "round_number": event.round_number,
        }
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/api/events/{self.session_id}",
                json={k: v for k, v in payload.items() if v is not None},
            )

    async def push_text(self, agent_name: str, text: str) -> None:
        """Push a text delta to the viewer."""
        if not self.session_id:
            return
        import httpx

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/api/events/{self.session_id}",
                json={"type": "text_delta", "agent_name": agent_name, "text": text},
            )

    async def push_result(self, markdown: str) -> None:
        """Push the final formatted result."""
        if not self.session_id:
            return
        import httpx

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/api/events/{self.session_id}",
                json={"type": "result", "markdown": markdown},
            )
            await client.post(
                f"{self.base_url}/api/events/{self.session_id}/done",
            )


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
    config = ConfigLoader.load(args.config)
    personas = PersonaLoader.load_all(args.personas_dir)
    custom = PersonaLoader.discover_custom(args.personas_dir)
    for p in custom:
        personas[p.name.lower().replace(" ", "-")] = p

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

    client = AsyncAnthropic()
    engine = DeliberationEngine(
        client=client,
        config=config,
        personas=personas,
        on_event=on_event,
        on_text=on_text if web else None,
    )

    result = await engine.run(args.question, args.preset)

    formatter = ResultFormatter(personas)
    formatted = formatter.format(result)

    if web:
        await web.push_result(formatted)

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

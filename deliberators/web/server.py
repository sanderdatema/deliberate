"""FastAPI server — display-only deliberation viewer.

The server does NOT run the engine itself. Events are pushed to it
by the engine running elsewhere (Claude Code, CLI with --web, etc.).

Architecture:
- CLI/Claude Code creates a session via POST /api/session
- CLI pushes events via POST /api/events/{session_id}
- Browser polls GET /api/latest-session to find the active session
- Browser connects WebSocket /ws/{session_id} to receive events
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Deliberators Viewer", description="Live deliberation viewer")

# Mount static files AFTER explicit routes (order matters)
# We'll do it at the bottom

# In-memory state
_queues: dict[str, asyncio.Queue[dict[str, Any] | None]] = {}
_latest_session_id: str | None = None


class SessionResponse(BaseModel):
    id: str
    ws_url: str


class EventPayload(BaseModel):
    type: str
    agent_name: str | None = None
    round_number: int | None = None
    text: str | None = None
    markdown: str | None = None
    message: str | None = None


@app.get("/")
async def index() -> HTMLResponse:
    """Serve the frontend."""
    index_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=index_path.read_text())


@app.get("/api/latest-session")
async def latest_session() -> dict[str, str | None]:
    """Return the most recently created session ID. Browser polls this."""
    return {"id": _latest_session_id}


@app.post("/api/session")
async def create_session() -> SessionResponse:
    """Create a new viewer session. Called by the CLI/Claude Code."""
    global _latest_session_id
    session_id = str(uuid.uuid4())[:8]
    _queues[session_id] = asyncio.Queue()
    _latest_session_id = session_id
    return SessionResponse(id=session_id, ws_url=f"/ws/{session_id}")


@app.post("/api/events/{session_id}")
async def push_event(session_id: str, event: EventPayload) -> dict[str, str]:
    """Push an event to a session. Called by the engine runner."""
    queue = _queues.get(session_id)
    if queue is None:
        return {"status": "unknown_session"}
    await queue.put(event.model_dump(exclude_none=True))
    return {"status": "ok"}


@app.post("/api/events/{session_id}/done")
async def push_done(session_id: str) -> dict[str, str]:
    """Signal that the deliberation is complete."""
    queue = _queues.get(session_id)
    if queue is None:
        return {"status": "unknown_session"}
    await queue.put(None)  # Sentinel
    return {"status": "ok"}


@app.websocket("/ws/{session_id}")
async def websocket_stream(websocket: WebSocket, session_id: str) -> None:
    """Stream events to the browser."""
    await websocket.accept()

    queue = _queues.get(session_id)
    if queue is None:
        await websocket.send_json({"type": "error", "message": "Unknown session"})
        await websocket.close()
        return

    try:
        while True:
            msg = await queue.get()
            if msg is None:
                break
            await websocket.send_json(msg)
    except WebSocketDisconnect:
        pass
    finally:
        _queues.pop(session_id, None)


# Mount static files last so explicit routes take precedence
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

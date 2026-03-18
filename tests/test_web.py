"""Tests for the web viewer server."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from deliberators.web.server import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


class TestIndexPage:
    def test_get_index_returns_html(self, client: TestClient) -> None:
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Deliberators" in resp.text
        assert "text/html" in resp.headers["content-type"]


class TestSessionAPI:
    def test_create_session(self, client: TestClient) -> None:
        resp = client.post("/api/session")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "ws_url" in data
        assert data["ws_url"].startswith("/ws/")

    def test_session_ids_are_unique(self, client: TestClient) -> None:
        r1 = client.post("/api/session").json()
        r2 = client.post("/api/session").json()
        assert r1["id"] != r2["id"]


class TestEventPush:
    def test_push_event_to_valid_session(self, client: TestClient) -> None:
        session = client.post("/api/session").json()
        resp = client.post(
            f"/api/events/{session['id']}",
            json={"type": "deliberation_started"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_push_event_to_unknown_session(self, client: TestClient) -> None:
        resp = client.post(
            "/api/events/nonexistent",
            json={"type": "deliberation_started"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "unknown_session"

    def test_push_text_delta(self, client: TestClient) -> None:
        session = client.post("/api/session").json()
        resp = client.post(
            f"/api/events/{session['id']}",
            json={"type": "text_delta", "agent_name": "socrates", "text": "Hello"},
        )
        assert resp.status_code == 200

    def test_push_done(self, client: TestClient) -> None:
        session = client.post("/api/session").json()
        resp = client.post(f"/api/events/{session['id']}/done")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_push_done_unknown_session(self, client: TestClient) -> None:
        resp = client.post("/api/events/nonexistent/done")
        assert resp.status_code == 200
        assert resp.json()["status"] == "unknown_session"

    def test_push_event_missing_type_returns_422(self, client: TestClient) -> None:
        session = client.post("/api/session").json()
        resp = client.post(
            f"/api/events/{session['id']}",
            json={"agent_name": "socrates"},  # Missing required 'type'
        )
        assert resp.status_code == 422


class TestWebSocketStream:
    def test_websocket_receives_pushed_events(self, client: TestClient) -> None:
        """Push events via HTTP, receive them via WebSocket."""
        session = client.post("/api/session").json()
        sid = session["id"]

        with client.websocket_connect(f"/ws/{sid}") as ws:
            # Push an event via HTTP
            client.post(
                f"/api/events/{sid}",
                json={"type": "deliberation_started"},
            )
            # Push done sentinel
            client.post(f"/api/events/{sid}/done")

            # WebSocket should receive the event
            msg = ws.receive_json()
            assert msg["type"] == "deliberation_started"

    def test_websocket_unknown_session(self, client: TestClient) -> None:
        with client.websocket_connect("/ws/nonexistent") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "error"
            assert "Unknown" in msg["message"]

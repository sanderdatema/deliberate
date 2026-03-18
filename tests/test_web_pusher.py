"""Tests for deliberators.web_pusher — HTTP push client with error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from deliberators.models import DeliberationEvent
from deliberators.web_pusher import WebPusher


@pytest.fixture()
def pusher() -> WebPusher:
    p = WebPusher("http://localhost:8000")
    p.session_id = "test-session"
    return p


class TestWebPusherErrorHandling:
    """WebPusher HTTP errors are caught gracefully — deliberation continues."""

    @pytest.mark.asyncio
    async def test_push_event_survives_connection_error(self, pusher: WebPusher) -> None:
        """push_event does not raise on connection failure."""
        pusher._client.post = AsyncMock(side_effect=ConnectionError("refused"))
        event = DeliberationEvent(type="deliberation_started")

        # Should not raise
        await pusher.push_event(event)

    @pytest.mark.asyncio
    async def test_push_text_survives_connection_error(self, pusher: WebPusher) -> None:
        """push_text does not raise on connection failure."""
        pusher._client.post = AsyncMock(side_effect=ConnectionError("refused"))

        await pusher.push_text("socrates", "Hello")

    @pytest.mark.asyncio
    async def test_push_result_survives_connection_error(self, pusher: WebPusher) -> None:
        """push_result does not raise on connection failure."""
        pusher._client.post = AsyncMock(side_effect=ConnectionError("refused"))

        await pusher.push_result("# Final result")

    @pytest.mark.asyncio
    async def test_push_event_logs_warning_on_error(
        self, pusher: WebPusher, caplog: pytest.LogCaptureFixture
    ) -> None:
        """HTTP errors are logged as warnings."""
        pusher._client.post = AsyncMock(side_effect=ConnectionError("refused"))
        event = DeliberationEvent(type="round_started", round_number=1)

        import logging
        with caplog.at_level(logging.WARNING, logger="deliberators.web_pusher"):
            await pusher.push_event(event)

        assert "Failed to push event" in caplog.text

    @pytest.mark.asyncio
    async def test_push_without_session_is_noop(self) -> None:
        """Push methods are no-ops when session_id is None."""
        pusher = WebPusher("http://localhost:8000")
        assert pusher.session_id is None

        # These should all return immediately without making HTTP calls
        await pusher.push_event(DeliberationEvent(type="deliberation_started"))
        await pusher.push_text("test", "hello")
        await pusher.push_result("result")


class TestWebPusherEventData:
    """WebPusher includes event.data in the HTTP payload."""

    @pytest.mark.asyncio
    async def test_push_event_includes_data(self, pusher: WebPusher) -> None:
        """Event data dict is forwarded to the server."""
        pusher._client.post = AsyncMock()
        event = DeliberationEvent(
            type="team_selected",
            data={"analysts": ["socrates", "occam"], "reason": "Good fit"},
        )
        await pusher.push_event(event)

        call_kwargs = pusher._client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["data"] == {"analysts": ["socrates", "occam"], "reason": "Good fit"}

    @pytest.mark.asyncio
    async def test_push_event_omits_data_when_empty(self, pusher: WebPusher) -> None:
        """Empty data dict is not included in payload."""
        pusher._client.post = AsyncMock()
        event = DeliberationEvent(type="deliberation_started")
        await pusher.push_event(event)

        call_kwargs = pusher._client.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "data" not in payload


class TestWebPusherTimeout:
    """WebPusher has a configured timeout on the HTTP client."""

    def test_client_has_timeout(self) -> None:
        """AsyncClient is created with a timeout."""
        pusher = WebPusher("http://localhost:8000")
        assert pusher._client.timeout.connect is not None

"""Push events to the web viewer server via HTTP."""

from __future__ import annotations

import logging

import httpx

from deliberators.models import DeliberationEvent

logger = logging.getLogger(__name__)


class WebPusher:
    """Push events to the web viewer server via HTTP."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session_id: str | None = None
        self._client: httpx.AsyncClient = httpx.AsyncClient(timeout=10.0)

    async def create_session(self) -> str:
        """Create a viewer session and return the session ID."""
        resp = await self._client.post(f"{self.base_url}/api/session")
        resp.raise_for_status()
        data = resp.json()
        self.session_id = data["id"]
        return self.session_id

    async def push_event(self, event: DeliberationEvent) -> None:
        """Push a DeliberationEvent to the viewer."""
        if not self.session_id:
            return
        try:
            payload = {
                "type": event.type,
                "agent_name": event.agent_name,
                "round_number": event.round_number,
            }
            await self._client.post(
                f"{self.base_url}/api/events/{self.session_id}",
                json={k: v for k, v in payload.items() if v is not None},
            )
        except Exception as e:
            logger.warning("Failed to push event to web viewer: %s", e)

    async def push_text(self, agent_name: str, text: str) -> None:
        """Push a text delta to the viewer."""
        if not self.session_id:
            return
        try:
            await self._client.post(
                f"{self.base_url}/api/events/{self.session_id}",
                json={"type": "text_delta", "agent_name": agent_name, "text": text},
            )
        except Exception as e:
            logger.warning("Failed to push text to web viewer: %s", e)

    async def push_result(self, markdown: str) -> None:
        """Push the final formatted result."""
        if not self.session_id:
            return
        try:
            await self._client.post(
                f"{self.base_url}/api/events/{self.session_id}",
                json={"type": "result", "markdown": markdown},
            )
            await self._client.post(
                f"{self.base_url}/api/events/{self.session_id}/done",
            )
        except Exception as e:
            logger.warning("Failed to push result to web viewer: %s", e)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

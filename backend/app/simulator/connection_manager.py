"""
Tracks active WebSocket connections and broadcasts simulator ticks to all
of them. Kept minimal on purpose — for a multi-instance production deploy
this would move to a Redis pub/sub backbone, but for a single-process
FastAPI app an in-memory list is correct and simple.
"""
import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._active.append(websocket)
        logger.info("WebSocket connected. Active connections: %d", len(self._active))

    def disconnect(self, websocket: WebSocket):
        if websocket in self._active:
            self._active.remove(websocket)
        logger.info("WebSocket disconnected. Active connections: %d", len(self._active))

    async def broadcast(self, payload: dict):
        """Send a JSON payload to every connected client, dropping any that
        have gone stale rather than letting one bad socket break the loop."""
        dead: list[WebSocket] = []
        for ws in self._active:
            try:
                await ws.send_text(json.dumps(payload, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


connection_manager = ConnectionManager()

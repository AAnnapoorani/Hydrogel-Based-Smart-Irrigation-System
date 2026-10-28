"""Real-Time WebSocket Connection Manager for IRRIGATEWISE.

Broadcasts live telemetry, pump state transitions, and anomaly alerts
to all connected browser clients for real-time dashboard telemetry visualization.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import WebSocket

class WebSocketManager:
    _instance: Optional["WebSocketManager"] = None
    active_connections: List[WebSocket] = []

    def __new__(cls) -> "WebSocketManager":
        if cls._instance is None:
            cls._instance = super(WebSocketManager, cls).__new__(cls)
            cls._instance.active_connections = []
        return cls._instance

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send initial welcome packet
        await websocket.send_text(json.dumps({
            "event": "CONNECTED",
            "message": "Connected to IRRIGATEWISE Real-Time Telemetry Stream",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_clients": len(self.active_connections)
        }))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, payload: Dict[str, Any]):
        """Asynchronously broadcasts event to all active WebSocket clients."""
        if not self.active_connections:
            return

        message = json.dumps({
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload
        }, default=str)

        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)

        for dead in dead_connections:
            self.disconnect(dead)

    def broadcast_sync(self, event_type: str, payload: Dict[str, Any]):
        """Synchronous wrapper to allow non-async route handlers and threads to broadcast."""
        if not self.active_connections:
            return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(event_type, payload), loop)
            else:
                loop.run_until_complete(self.broadcast(event_type, payload))
        except RuntimeError:
            # If called from a thread without an active loop, launch a one-off thread or loop
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(self.broadcast(event_type, payload))
                new_loop.close()
            except Exception as e:
                print(f"WebSocket broadcast_sync error: {e}")

ws_manager = WebSocketManager()

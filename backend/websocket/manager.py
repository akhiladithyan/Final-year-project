import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("websocket")

class ConnectionManager:
    """Manages active WebSocket connections from frontend clients."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_json(self, message: Dict[str, Any]):
        """Broadcasts a JSON serializable dictionary to all active clients."""
        if not self.active_connections:
            return

        payload = json.dumps(message)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                dead_connections.append(connection)

        for dead in dead_connections:
            if dead in self.active_connections:
                self.active_connections.remove(dead)

    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        """Broadcasts an alert event to all clients."""
        await self.broadcast_json({
            "type": "alert",
            "data": alert_data
        })

    async def broadcast_telemetry(self, telemetry_data: Dict[str, Any]):
        """Broadcasts real-time detection, tracking, and pose data for a frame."""
        await self.broadcast_json({
            "type": "telemetry",
            "data": telemetry_data
        })

ws_manager = ConnectionManager()

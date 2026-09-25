"""
WebSocket Telemetry and State Broadcasting Manager.
Streams LangGraph node transitions and live extraction records to client dashboards.
"""
import json
import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger("WebSocketManager")

class ConnectionManager:
    def __init__(self):
        # Map workflow_id -> list of connected WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Global watchers
        self.global_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, workflow_id: str = "global"):
        await websocket.accept()
        if workflow_id == "global":
            self.global_connections.append(websocket)
        else:
            if workflow_id not in self.active_connections:
                self.active_connections[workflow_id] = []
            self.active_connections[workflow_id].append(websocket)
        logger.info(f"Client connected to telemetry room: {workflow_id}")

    def disconnect(self, websocket: WebSocket, workflow_id: str = "global"):
        if workflow_id == "global":
            if websocket in self.global_connections:
                self.global_connections.remove(websocket)
        elif workflow_id in self.active_connections:
            if websocket in self.active_connections[workflow_id]:
                self.active_connections[workflow_id].remove(websocket)
                if not self.active_connections[workflow_id]:
                    del self.active_connections[workflow_id]
        logger.info(f"Client disconnected from telemetry room: {workflow_id}")

    async def broadcast_to_workflow(self, workflow_id: str, message: Dict[str, Any]):
        payload = json.dumps(message)
        
        # Broadcast to specific workflow listeners
        if workflow_id in self.active_connections:
            for connection in list(self.active_connections[workflow_id]):
                try:
                    await connection.send_text(payload)
                except Exception:
                    self.disconnect(connection, workflow_id)

        # Broadcast to global dashboard monitors
        for connection in list(self.global_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                self.disconnect(connection, "global")

ws_manager = ConnectionManager()

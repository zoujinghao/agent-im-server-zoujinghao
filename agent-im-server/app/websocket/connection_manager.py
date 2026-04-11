import asyncio
import json
from typing import Dict, Set, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Store connections by conversation_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: int):
        """Connect a WebSocket to a conversation"""
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = set()
        self.active_connections[conversation_id].add(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: int):
        """Disconnect a WebSocket from a conversation"""
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].discard(websocket)
            # Clean up empty conversation sets
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_text(message)
        except Exception:
            # Handle disconnected clients
            pass

    async def broadcast_to_conversation(self, conversation_id: int, message: str):
        """Broadcast a message to all WebSockets in a conversation"""
        if conversation_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[conversation_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    # Client disconnected
                    disconnected.add(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.active_connections[conversation_id].discard(conn)
            
            # Clean up empty conversation sets
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    def get_conversation_connections(self, conversation_id: int) -> Set[WebSocket]:
        """Get all active connections for a conversation"""
        return self.active_connections.get(conversation_id, set())
import asyncio
import json
from typing import Dict, Set, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Store connections by conversation_id
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Lock to protect concurrent access to active_connections
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, conversation_id: int):
        """Connect a WebSocket to a conversation"""
        await websocket.accept()
        async with self._lock:
            if conversation_id not in self.active_connections:
                self.active_connections[conversation_id] = set()
            self.active_connections[conversation_id].add(websocket)

    def disconnect(self, websocket: WebSocket, conversation_id: int):
        """Disconnect a WebSocket from a conversation"""
        # This method is called from exception handler and may not be in async context
        # Use synchronous lock if possible, but for simplicity we'll use the async lock
        # In practice, this should be called from an async context
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, use the lock
            async def _disconnect():
                async with self._lock:
                    if conversation_id in self.active_connections:
                        self.active_connections[conversation_id].discard(websocket)
                        # Clean up empty conversation sets
                        if not self.active_connections[conversation_id]:
                            del self.active_connections[conversation_id]
            # Schedule the disconnect operation
            asyncio.create_task(_disconnect())
        except RuntimeError:
            # Not in async context, handle synchronously (less safe but necessary)
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
        async with self._lock:
            if conversation_id not in self.active_connections:
                return
            
            # Create a copy of the connections set to avoid modification during iteration
            connections_copy = self.active_connections[conversation_id].copy()
        
        disconnected = set()
        for connection in connections_copy:
            try:
                await connection.send_text(message)
            except Exception:
                # Client disconnected
                disconnected.add(connection)
        
        # Remove disconnected clients
        if disconnected:
            async with self._lock:
                if conversation_id in self.active_connections:
                    self.active_connections[conversation_id] -= disconnected
                    # Clean up empty conversation sets
                    if not self.active_connections[conversation_id]:
                        del self.active_connections[conversation_id]

    def get_conversation_connections(self, conversation_id: int) -> Set[WebSocket]:
        """Get all active connections for a conversation"""
        # This is read-only, but to be safe we should use the lock
        # However, since it returns a copy and is only used internally,
        # and to avoid making it async, we'll return a copy without lock
        # In high-concurrency scenarios, this might return slightly stale data
        # but that's acceptable for this use case
        connections = self.active_connections.get(conversation_id, set())
        return connections.copy()
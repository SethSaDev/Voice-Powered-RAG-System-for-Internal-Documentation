"""
WebSocket Connection Manager
Handles active connections, broadcasting, and connection lifecycle
"""

import asyncio
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and message routing
    """
    
    def __init__(self):
        # Active connections: {client_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # User to client mapping: {user_id: set(client_ids)}
        self.user_connections: Dict[str, Set[str]] = {}
        # Connection metadata
        self.connection_metadata: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, user_id: Optional[str] = None):
        """
        Accept and register a new WebSocket connection
        """
        await websocket.accept()
        
        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "last_heartbeat": datetime.utcnow().isoformat(),
        }
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(client_id)
        
        logger.info(f"WebSocket connected: client_id={client_id}, user_id={user_id}, total={len(self.active_connections)}")
        
        # Send connection confirmation
        await self.send_json(client_id, {
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def disconnect(self, client_id: str):
        """
        Remove a WebSocket connection
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from user mapping
        metadata = self.connection_metadata.get(client_id, {})
        user_id = metadata.get("user_id")
        
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(client_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove metadata
        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]
        
        logger.info(f"WebSocket disconnected: client_id={client_id}, remaining={len(self.active_connections)}")
    
    async def send_json(self, client_id: str, data: dict):
        """
        Send JSON data to a specific client
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(data)
            except Exception as e:
                logger.error(f"Failed to send to client {client_id}: {e}")
                self.disconnect(client_id)
    
    async def send_text(self, client_id: str, text: str):
        """
        Send raw text to a specific client
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(text)
            except Exception as e:
                logger.error(f"Failed to send text to client {client_id}: {e}")
                self.disconnect(client_id)
    
    async def send_bytes(self, client_id: str, data: bytes):
        """
        Send binary data (audio) to a specific client
        """
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_bytes(data)
            except Exception as e:
                logger.error(f"Failed to send bytes to client {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_to_user(self, user_id: str, data: dict):
        """
        Broadcast a message to all connections of a specific user
        """
        if user_id in self.user_connections:
            for client_id in self.user_connections[user_id]:
                await self.send_json(client_id, data)
    
    async def broadcast_to_all(self, data: dict):
        """
        Broadcast a message to all connected clients
        """
        for client_id in self.active_connections:
            await self.send_json(client_id, data)
    
    async def send_audio_stream(self, client_id: str, audio_chunk: bytes, chunk_index: int, total_chunks: int):
        """
        Send streaming audio data with metadata
        """
        message = {
            "type": "audio_stream",
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Send metadata as JSON, then audio bytes
        await self.send_json(client_id, message)
        await self.send_bytes(client_id, audio_chunk)
    
    async def update_heartbeat(self, client_id: str):
        """
        Update last heartbeat timestamp for a connection
        """
        if client_id in self.connection_metadata:
            self.connection_metadata[client_id]["last_heartbeat"] = datetime.utcnow().isoformat()
    
    def get_connection_count(self) -> int:
        """
        Get total number of active connections
        """
        return len(self.active_connections)
    
    def get_user_connection_count(self, user_id: str) -> int:
        """
        Get number of active connections for a specific user
        """
        return len(self.user_connections.get(user_id, set()))
    
    async def close_all_connections(self):
        """
        Close all active connections during shutdown
        """
        for client_id in list(self.active_connections.keys()):
            try:
                await self.active_connections[client_id].close(code=1001, reason="Server shutting down")
            except Exception as e:
                logger.error(f"Error closing connection {client_id}: {e}")
            finally:
                self.disconnect(client_id)
        
        logger.info(f"All connections closed. Final count: {len(self.active_connections)}")


# Global connection manager instance
manager = ConnectionManager()
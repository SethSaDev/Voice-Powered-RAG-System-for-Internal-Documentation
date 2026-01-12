import json
import logging
from typing import Optional
from fastapi import WebSocket
from api.websocket.connection_manager import manager

logger = logging.getLogger(__name__)

class WebSocketHandler:
    """Handles WebSocket messages"""
    
    async def handle_connection(self, websocket: WebSocket, client_id: str, user_id: Optional[str] = None):
        await manager.connect(websocket, client_id, user_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                logger.info(f"Received message from {client_id}: {message.get('type', 'unknown')}")
                
                # Echo back for now
                await manager.send_json(client_id, {"type": "echo", "data": message})
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
        finally:
            manager.disconnect(client_id)

ws_handler = WebSocketHandler()

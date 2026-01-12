from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.websocket.handlers import ws_handler

router = APIRouter()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await ws_handler.handle_connection(websocket, client_id)

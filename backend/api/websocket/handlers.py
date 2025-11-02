"""
WebSocket Message Handlers
Process incoming voice data and orchestrate the RAG pipeline
"""

import json
import base64
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.websocket.connection_manager import manager
from core.database import get_db
from core.redis_client import redis_client
from services.voice_pipeline.transcriber import transcriber
from services.voice_pipeline.synthesizer import synthesizer
from services.rag_engine.retriever import retriever
from services.rag_engine.context_builder import context_builder
from services.llm.chat_completion import llm_chat
from models.conversation import Conversation
from models.message import Message
from models.user import User

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """
    Handles WebSocket messages and orchestrates voice AI processing
    """
    
    def __init__(self):
        self.active_processing: Dict[str, bool] = {}  # client_id -> is_processing
    
    async def handle_connection(self, websocket: WebSocket, client_id: str, user_id: Optional[str] = None):
        """
        Main WebSocket handler for a client connection
        """
        await manager.connect(websocket, client_id, user_id)
        
        try:
            while True:
                # Receive message from client
                message = await websocket.receive()
                
                # Handle text messages (JSON commands)
                if "text" in message:
                    await self.handle_text_message(client_id, message["text"], user_id)
                
                # Handle binary messages (audio data)
                elif "bytes" in message:
                    await self.handle_audio_message(client_id, message["bytes"], user_id)
                
                # Handle heartbeat
                await manager.update_heartbeat(client_id)
                
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling WebSocket for {client_id}: {e}")
        finally:
            manager.disconnect(client_id)
    
    async def handle_text_message(self, client_id: str, text: str, user_id: Optional[str]):
        """
        Handle incoming text messages (commands or text queries)
        """
        try:
            data = json.loads(text)
            message_type = data.get("type")
            
            if message_type == "ping":
                await manager.send_json(client_id, {"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            
            elif message_type == "text_query":
                query = data.get("query", "")
                conversation_id = data.get("conversation_id")
                await self.process_text_query(client_id, query, conversation_id, user_id)
            
            elif message_type == "end_of_audio":
                # Client finished sending audio stream
                await manager.send_json(client_id, {"type": "processing_started"})
            
            elif message_type == "feedback":
                # User feedback on response
                message_id = data.get("message_id")
                feedback = data.get("feedback")  # 1 = positive, -1 = negative
                await self.store_feedback(message_id, feedback)
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client {client_id}: {text}")
            await manager.send_json(client_id, {"type": "error", "message": "Invalid JSON"})
    
    async def handle_audio_message(self, client_id: str, audio_bytes: bytes, user_id: Optional[str]):
        """
        Handle incoming audio data, transcribe, and process query
        """
        # Prevent concurrent processing for same client
        if self.active_processing.get(client_id, False):
            logger.warning(f"Client {client_id} already processing, ignoring")
            return
        
        self.active_processing[client_id] = True
        
        try:
            # Notify client that processing started
            await manager.send_json(client_id, {"type": "transcribing_started"})
            
            # Step 1: Transcribe audio to text
            transcribed_text = await transcriber.transcribe(audio_bytes)
            
            if not transcribed_text:
                await manager.send_json(client_id, {
                    "type": "error",
                    "message": "Could not transcribe audio. Please try again."
                })
                return
            
            # Send transcription result
            await manager.send_json(client_id, {
                "type": "transcription_complete",
                "text": transcribed_text,
            })
            
            # Step 2: Process the text query
            await self.process_text_query(client_id, transcribed_text, None, user_id)
            
        except Exception as e:
            logger.error(f"Error processing audio for {client_id}: {e}")
            await manager.send_json(client_id, {
                "type": "error",
                "message": f"Processing error: {str(e)}"
            })
        finally:
            self.active_processing[client_id] = False
    
    async def process_text_query(
        self,
        client_id: str,
        query: str,
        conversation_id: Optional[str],
        user_id: Optional[str]
    ):
        """
        Core RAG pipeline: Retrieve context, generate response, synthesize speech
        """
        start_time = datetime.utcnow()
        
        try:
            # Notify client
            await manager.send_json(client_id, {"type": "retrieving_started"})
            
            # Step 1: Generate embedding for query
            query_embedding = await retriever.get_embedding(query)
            
            # Step 2: Retrieve relevant documents
            retrieved_chunks = await retriever.similarity_search(
                query_embedding=query_embedding,
                top_k=5,
            )
            
            # Step 3: Build context from retrieved chunks
            context = context_builder.build_context(retrieved_chunks)
            
            # Notify client
            await manager.send_json(client_id, {
                "type": "generating_started",
                "retrieved_chunks_count": len(retrieved_chunks),
            })
            
            # Step 4: Generate response using LLM
            response_text = await llm_chat.generate_response(
                query=query,
                context=context,
                conversation_history=None,  # Would fetch from DB
            )
            
            # Step 5: Generate audio from response
            await manager.send_json(client_id, {"type": "synthesizing_started"})
            
            audio_response = await synthesizer.synthesize(response_text)
            
            # Step 6: Store conversation in database (if user authenticated)
            message_id = None
            if user_id:
                message_id = await self.store_conversation(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    query=query,
                    response=response_text,
                    retrieved_chunks=retrieved_chunks,
                    processing_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                )
            
            # Step 7: Send response to client
            await manager.send_json(client_id, {
                "type": "response_text",
                "text": response_text,
                "message_id": message_id,
                "processing_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000),
            })
            
            # Step 8: Stream audio response in chunks
            if audio_response:
                # Send audio in chunks (if streaming) or as single blob
                await manager.send_bytes(client_id, audio_response)
                
                await manager.send_json(client_id, {
                    "type": "response_complete",
                    "audio_duration_ms": len(audio_response) // 160,  # Rough estimate for 16kHz MP3
                })
            else:
                await manager.send_json(client_id, {
                    "type": "error",
                    "message": "Failed to generate audio response",
                })
            
        except Exception as e:
            logger.error(f"Error processing query for {client_id}: {e}")
            await manager.send_json(client_id, {
                "type": "error",
                "message": f"Query processing failed: {str(e)}",
            })
    
    async def store_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str],
        query: str,
        response: str,
        retrieved_chunks: list,
        processing_time_ms: int,
    ) -> Optional[str]:
        """
        Store conversation history in database
        """
        try:
            from sqlalchemy.ext.asyncio import AsyncSession
            from core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as db:
                # Get or create conversation
                if not conversation_id:
                    # Create new conversation
                    conversation = Conversation(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        title=query[:100],  # First 100 chars as title
                    )
                    db.add(conversation)
                    await db.flush()
                    conversation_id = conversation.id
                
                # Store user message
                user_message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    role="user",
                    content=query,
                )
                db.add(user_message)
                
                # Store assistant message with RAG metadata
                assistant_message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    role="assistant",
                    content=response,
                    retrieved_chunks=[
                        {
                            "text": chunk.get("text", "")[:200],
                            "score": chunk.get("similarity_score", 0),
                            "source": chunk.get("metadata", {}).get("source", "unknown"),
                        }
                        for chunk in retrieved_chunks
                    ],
                    confidence_score=0.85,  # Placeholder
                    processing_time_ms=processing_time_ms,
                )
                db.add(assistant_message)
                
                # Update conversation
                conversation.message_count = conversation.message_count + 2
                conversation.last_message_at = datetime.utcnow()
                
                await db.commit()
                
                return assistant_message.id
                
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            return None
    
    async def store_feedback(self, message_id: str, feedback: int):
        """
        Store user feedback on assistant response
        """
        try:
            from sqlalchemy.ext.asyncio import AsyncSession
            from core.database import AsyncSessionLocal
            from sqlalchemy import update
            
            async with AsyncSessionLocal() as db:
                stmt = update(Message).where(Message.id == message_id).values(user_feedback=feedback)
                await db.execute(stmt)
                await db.commit()
                
                logger.info(f"Feedback stored for message {message_id}: {feedback}")
        except Exception as e:
            logger.error(f"Failed to store feedback: {e}")


# Global WebSocket handler instance
ws_handler = WebSocketHandler()
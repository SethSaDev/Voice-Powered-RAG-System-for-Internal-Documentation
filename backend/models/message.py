"""
Message Model - Individual Chat Messages
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from core.database import Base


class Message(Base):
    """Individual message in a conversation"""
    
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    
    # RAG metadata (for assistant messages)
    retrieved_chunks = Column(JSON, nullable=True)  # Array of retrieved document chunks
    confidence_score = Column(Float, nullable=True)  # Model confidence
    processing_time_ms = Column(Integer, nullable=True)  # Time to generate response
    
    # Audio metadata (for voice messages)
    audio_duration_ms = Column(Integer, nullable=True)
    audio_file_path = Column(String(500), nullable=True)  # S3 or local path
    
    # Feedback
    user_feedback = Column(Integer, nullable=True)  # 1=positive, -1=negative, None=none
    
    # Timestamp
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.id[:8]} - {self.role}>"
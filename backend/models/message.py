"""
Message Model - Individual Chat Messages
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from core.database import Base

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    retrieved_chunks = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    user_feedback = Column(Integer, nullable=True)  # 1=positive, -1=negative
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    conversation = relationship("Conversation", back_populates="messages")

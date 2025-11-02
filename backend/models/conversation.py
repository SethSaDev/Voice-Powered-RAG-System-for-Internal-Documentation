"""
Conversation Model - Chat Session Management
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from core.database import Base


class Conversation(Base):
    """Conversation session model"""
    
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), default="New Conversation")
    
    # Metadata
    message_count = Column(Integer, default=0)
    total_duration_ms = Column(Integer, default=0)  # Total conversation time
    is_active = Column(Boolean, default=True)
    
    # Context window
    system_prompt = Column(Text, nullable=True)  # Custom system prompt for this conversation
    
    # Timestamps
    last_message_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    ended_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation {self.id[:8]} - {self.title}>"
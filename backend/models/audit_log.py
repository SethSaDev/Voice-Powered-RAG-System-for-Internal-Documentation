"""
Audit Log Model - Track All Actions for Compliance
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from core.database import Base


class AuditLog(Base):
    """Audit trail for all user actions"""
    
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)  # Null for system actions
    
    # Action details
    action_type = Column(String(50), nullable=False)  # login, query_document, upload_file, etc.
    resource_type = Column(String(50), nullable=True)  # document, conversation, user
    resource_id = Column(String(36), nullable=True)
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # Additional metadata
    
    # Result
    status = Column(String(20), nullable=False)  # success, failure, pending
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog {self.action_type} - {self.created_at}>"
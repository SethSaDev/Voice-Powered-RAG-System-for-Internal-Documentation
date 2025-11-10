"""
Audit Log Model - Track All Actions for Compliance
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action_type = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=True)
    details = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    
    user = relationship("User", back_populates="audit_logs")

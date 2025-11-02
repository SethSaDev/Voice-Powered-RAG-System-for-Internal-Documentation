"""
Document Model - Knowledge Base Document Management
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from core.database import Base


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    HTML = "html"


class Document(Base):
    """Document metadata model"""
    
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_type = Column(SQLEnum(DocumentType), nullable=False)
    
    # Storage paths
    s3_path = Column(String(500), nullable=True)  # For production S3
    local_path = Column(String(500), nullable=True)  # For local development
    
    # Processing metadata
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    total_chunks = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Document metadata
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    page_count = Column(Integer, nullable=True)
    
    # Processing timestamps
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    uploaded_by_user = relationship("User", back_populates="uploaded_documents")
    
    # Indexes (commented - would be in migration)
    # __table_args__ = (Index('idx_document_status', 'status'),)
    
    def __repr__(self):
        return f"<Document {self.filename} - {self.status}>"
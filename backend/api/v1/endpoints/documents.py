"""
Document Management Endpoints
Upload, list, delete, and reindex documents
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import os
import shutil
from pathlib import Path
import logging

from core.config import settings
from core.database import get_db
from core.vector_store import vector_store
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from models.document import Document, DocumentStatus, DocumentType
from models.user import User
from api.v1.endpoints.auth import get_current_user
from tasks.document_tasks import process_document_task

logger = logging.getLogger(__name__)
router = APIRouter()


# Response schemas
class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size_bytes: int
    file_type: str
    status: str
    total_chunks: int
    title: Optional[str]
    description: Optional[str]
    created_at: datetime
    processing_completed_at: Optional[datetime]
    error_message: Optional[str]


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str


# File upload configuration
UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    DocumentType.PDF: [".pdf"],
    DocumentType.DOCX: [".docx", ".doc"],
    DocumentType.TXT: [".txt"],
    DocumentType.MD: [".md"],
    DocumentType.HTML: [".html", ".htm"],
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def get_document_type(filename: str) -> DocumentType:
    """Determine document type from filename extension"""
    ext = Path(filename).suffix.lower()
    
    for doc_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return doc_type
    
    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}",
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document to be indexed in the knowledge base
    """
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset position
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Validate file type
    try:
        doc_type = get_document_type(file.filename)
    except HTTPException as e:
        raise e
    
    # Generate unique ID and save file
    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    
    # Create document record in database
    document = Document(
        id=doc_id,
        filename=safe_filename,
        original_filename=file.filename,
        file_size_bytes=file_size,
        file_type=doc_type,
        status=DocumentStatus.PENDING,
        title=title or file.filename,
        description=description,
        uploaded_by=current_user.id,
        local_path=str(file_path),
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Trigger async document processing
    background_tasks.add_task(
        process_document_task.delay,
        document_id=doc_id,
    )
    
    logger.info(f"Document uploaded: {doc_id} by user {current_user.id}")
    
    return DocumentUploadResponse(
        document_id=doc_id,
        filename=file.filename,
        status="pending",
        message="Document uploaded successfully. Processing in background.",
    )


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents with pagination and filtering"""
    
    query = select(Document).where(Document.uploaded_by == current_user.id)
    
    if status:
        query = query.where(Document.status == status)
    
    query = query.offset(skip).limit(limit).order_by(Document.created_at.desc())
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return [
        DocumentResponse(
            id=doc.id,
            filename=doc.original_filename,
            original_filename=doc.original_filename,
            file_size_bytes=doc.file_size_bytes,
            file_type=doc.file_type.value,
            status=doc.status.value,
            total_chunks=doc.total_chunks,
            title=doc.title,
            description=doc.description,
            created_at=doc.created_at,
            processing_completed_at=doc.processing_completed_at,
            error_message=doc.error_message,
        )
        for doc in documents
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document details by ID"""
    
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.uploaded_by == current_user.id,
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        id=document.id,
        filename=document.original_filename,
        original_filename=document.original_filename,
        file_size_bytes=document.file_size_bytes,
        file_type=document.file_type.value,
        status=document.status.value,
        total_chunks=document.total_chunks,
        title=document.title,
        description=document.description,
        created_at=document.created_at,
        processing_completed_at=document.processing_completed_at,
        error_message=document.error_message,
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and remove from vector store"""
    
    # Get document
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.uploaded_by == current_user.id,
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from vector store
    await vector_store.delete_document(document_id)
    
    # Delete physical file
    if document.local_path and Path(document.local_path).exists():
        Path(document.local_path).unlink()
    
    # Delete from database
    await db.delete(document)
    await db.commit()
    
    logger.info(f"Document deleted: {document_id} by user {current_user.id}")
    
    return {"message": "Document deleted successfully"}


@router.post("/{document_id}/reindex")
async def reindex_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-index a document (useful if processing failed)"""
    
    # Check if document exists and belongs to user
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.uploaded_by == current_user.id,
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Reset status and reprocess
    document.status = DocumentStatus.PENDING
    document.error_message = None
    document.processing_started_at = None
    document.processing_completed_at = None
    await db.commit()
    
    # Trigger reprocessing
    process_document_task.delay(document_id=document_id)
    
    return {"message": "Document re-indexing started"}
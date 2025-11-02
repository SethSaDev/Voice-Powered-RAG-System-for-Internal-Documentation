"""
Celery Tasks for Async Document Processing
Handles document ingestion, chunking, embedding generation, and vector storage
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import uuid

from celery import Task
from celery_app import celery_app
from core.config import settings
from core.database import AsyncSessionLocal
from core.vector_store import vector_store
from models.document import Document, DocumentStatus
from services.document_processing.extractor import extract_text_from_document
from services.document_processing.chunker import chunk_text
from services.rag_engine.embedder import embedder

logger = logging.getLogger(__name__)


class DocumentProcessingTask(Task):
    """
    Custom task class with database session handling
    """
    
    async def update_document_status(self, doc_id: str, status: DocumentStatus, error: str = None):
        """Update document status in database"""
        from sqlalchemy import update
        
        async with AsyncSessionLocal() as db:
            stmt = update(Document).where(Document.id == doc_id).values(
                status=status,
                error_message=error,
                processing_completed_at=datetime.utcnow() if status == DocumentStatus.COMPLETED else None,
            )
            await db.execute(stmt)
            await db.commit()


@celery_app.task(base=DocumentProcessingTask, bind=True, name="tasks.document_tasks.process_document")
def process_document_task(self, document_id: str):
    """
    Main task to process an uploaded document:
    1. Extract text from document
    2. Chunk text into segments
    3. Generate embeddings for each chunk
    4. Store in vector database
    5. Update document metadata
    """
    import asyncio
    
    # Run async tasks within the Celery task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(
            _process_document_async(document_id, self)
        )
        return result
    except Exception as e:
        logger.error(f"Document processing failed for {document_id}: {e}")
        # Update status to failed
        loop.run_until_complete(
            self.update_document_status(document_id, DocumentStatus.FAILED, str(e))
        )
        raise
    finally:
        loop.close()


async def _process_document_async(document_id: str, task: DocumentProcessingTask):
    """
    Async implementation of document processing
    """
    logger.info(f"Starting document processing for {document_id}")
    
    # Update status to processing
    await task.update_document_status(document_id, DocumentStatus.PROCESSING)
    
    # Get document from database
    from sqlalchemy import select
    from models.document import Document
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        file_path = document.local_path
        doc_type = document.file_type
        
        if not file_path or not Path(file_path).exists():
            raise ValueError(f"Document file not found at {file_path}")
    
    try:
        # Step 1: Extract text from document
        logger.info(f"Extracting text from {file_path}")
        extracted_text = await extract_text_from_document(file_path, doc_type.value)
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            raise ValueError(f"Extracted text too short or empty: {len(extracted_text)} chars")
        
        logger.info(f"Extracted {len(extracted_text)} characters")
        
        # Step 2: Chunk text into segments
        chunks = await chunk_text(extracted_text, chunk_size=500, overlap=50)
        
        if not chunks:
            raise ValueError("No chunks generated from document")
        
        logger.info(f"Generated {len(chunks)} chunks")
        
        # Step 3: Generate embeddings for each chunk
        embeddings = await embedder.get_embeddings_batch(chunks)
        
        # Filter out failed embeddings
        valid_chunks = []
        valid_embeddings = []
        valid_ids = []
        valid_metadatas = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding is not None:
                chunk_id = f"{document_id}_chunk_{i}"
                valid_chunks.append(chunk)
                valid_embeddings.append(embedding)
                valid_ids.append(chunk_id)
                valid_metadatas.append({
                    "document_id": document_id,
                    "filename": document.original_filename,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "source": document.original_filename,
                })
        
        if not valid_chunks:
            raise ValueError("No valid embeddings generated")
        
        logger.info(f"Generated {len(valid_chunks)} valid embeddings")
        
        # Step 4: Store in vector database
        await vector_store.initialize()
        await vector_store.add_documents(
            ids=valid_ids,
            embeddings=valid_embeddings,
            metadatas=valid_metadatas,
            documents=valid_chunks,
        )
        
        # Step 5: Update document metadata in database
        async with AsyncSessionLocal() as db:
            from sqlalchemy import update
            
            stmt = update(Document).where(Document.id == document_id).values(
                status=DocumentStatus.COMPLETED,
                total_chunks=len(valid_chunks),
                processing_completed_at=datetime.utcnow(),
            )
            await db.execute(stmt)
            await db.commit()
        
        logger.info(f"Document {document_id} processed successfully with {len(valid_chunks)} chunks")
        
        return {
            "document_id": document_id,
            "status": "completed",
            "chunks": len(valid_chunks),
        }
        
    except Exception as e:
        logger.error(f"Document processing failed for {document_id}: {e}")
        raise


@celery_app.task(name="tasks.document_tasks.reprocess_failed_documents")
def reprocess_failed_documents_task():
    """
    Reprocess all failed documents
    """
    import asyncio
    from sqlalchemy import select
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Document).where(Document.status == DocumentStatus.FAILED)
            )
            failed_docs = result.scalars().all()
            
            for doc in failed_docs:
                logger.info(f"Reprocessing failed document: {doc.id}")
                process_document_task.delay(doc.id)
            
            return {"reprocessed": len(failed_docs)}
    finally:
        loop.close()
import logging
from celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.document_tasks.process_document")
def process_document_task(document_id: str):
    """Main task to process uploaded documents"""
    logger.info(f"Processing document {document_id}")
    # Placeholder for actual document processing
    return {"document_id": document_id, "status": "completed"}

@celery_app.task(name="tasks.document_tasks.reprocess_failed_documents")
def reprocess_failed_documents_task():
    """Reprocess all failed documents"""
    logger.info("Reprocessing failed documents")
    return {"reprocessed": 0}

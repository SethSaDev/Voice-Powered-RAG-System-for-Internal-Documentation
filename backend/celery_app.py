from celery import Celery

celery_app = Celery(
    "voice_knowledge_base",
    broker="pyamqp://guest:guest@localhost:5672//",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
)

@celery_app.task
def process_document_task(document_id: str):
    """Process document in background"""
    return f"Document {document_id} processed successfully"

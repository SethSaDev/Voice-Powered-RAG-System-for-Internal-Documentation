import logging
from typing import List

logger = logging.getLogger(__name__)

async def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[str]:
    """Split text into overlapping chunks"""
    if not text or len(text) < chunk_size:
        return [text] if text else []
    
    # Simple chunking for now
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if chunk:
            chunks.append(chunk)
    
    logger.info(f"Created {len(chunks)} chunks")
    return chunks

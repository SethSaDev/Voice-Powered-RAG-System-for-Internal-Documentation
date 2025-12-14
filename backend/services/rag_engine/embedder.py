import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class Embedder:
    """Generate embeddings for text"""
    
    def __init__(self):
        self.model = "text-embedding-3-small"
        self.dimensions = 1536
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for single text"""
        logger.info(f"Generating embedding for {len(text)} characters")
        # Placeholder - return zero vector
        return [0.0] * self.dimensions

embedder = Embedder()

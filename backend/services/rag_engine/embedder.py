"""
Embedding Service using OpenAI Embeddings API
Converts text to vector representations for similarity search
"""

import logging
from typing import List, Optional
import asyncio

import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings

logger = logging.getLogger(__name__)


class Embedder:
    """
    Generates embeddings for text chunks and queries
    """
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self.dimensions = 1536  # text-embedding-3-small
        self.batch_size = 100  # Max embeddings per API call
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for a single text
        
        Args:
            text: Input text to embed
        
        Returns:
            Vector embedding (list of floats) or None if failed
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float",
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Get embeddings for multiple texts in batch
        
        Args:
            texts: List of input texts
        
        Returns:
            List of embeddings (None for failed texts)
        """
        if not texts:
            return []
        
        results = []
        
        # Process in batches to avoid API limits
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    encoding_format="float",
                )
                
                # Ensure results are in the same order as input
                batch_results = [data.embedding for data in response.data]
                results.extend(batch_results)
                
                logger.info(f"Generated {len(batch_results)} embeddings for batch")
                
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                results.extend([None] * len(batch))
            
            # Rate limiting between batches
            await asyncio.sleep(0.1)
        
        return results
    
    async def get_query_embedding(self, query: str) -> Optional[List[float]]:
        """
        Specialized method for query embeddings
        (Same as get_embedding but with potential query-specific preprocessing)
        """
        # For OpenAI, query embeddings use the same model
        return await self.get_embedding(query)


# Global embedder instance
embedder = Embedder()
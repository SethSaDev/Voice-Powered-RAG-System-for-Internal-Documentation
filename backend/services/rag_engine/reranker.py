"""
Re-ranking Service - Improves retrieval quality using cross-encoders
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class Reranker:
    """
    Re-ranks retrieved documents using cross-encoder models
    """
    
    def __init__(self):
        self.model = None
        self.model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
        self.enabled = False  # Set to True if local model is available
        
        # Attempt to load model if needed
        if self.enabled:
            self._load_model()
    
    def _load_model(self):
        """
        Load cross-encoder model (requires sentence-transformers)
        """
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name)
            logger.info(f"Loaded reranker model: {self.model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed. Reranking disabled.")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to load reranker model: {e}")
            self.enabled = False
    
    async def rerank(
        self,
        documents: List[Dict[str, Any]],
        query_embedding: Optional[List[float]] = None,
        query_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Re-rank documents based on relevance to query
        
        Args:
            documents: List of retrieved documents
            query_embedding: Query vector (optional)
            query_text: Query text (required if no embedding provided)
        
        Returns:
            Re-ranked document list
        """
        if not self.enabled or not documents:
            return documents
        
        # If no query text provided, we need to approximate from embedding
        # For now, return original order
        if not query_text:
            logger.warning("Cannot rerank without query text")
            return documents
        
        try:
            # Prepare pairs for cross-encoder
            pairs = [(query_text, doc.get("text", "")) for doc in documents]
            
            # Run reranking asynchronously to avoid blocking
            scores = await asyncio.to_thread(self.model.predict, pairs)
            
            # Sort documents by new scores
            for doc, score in zip(documents, scores):
                doc["rerank_score"] = float(score)
                # Combine with original similarity score
                doc["combined_score"] = (
                    doc.get("similarity_score", 0) * 0.3 + 
                    float(score) * 0.7
                )
            
            # Sort by combined score
            reranked = sorted(
                documents,
                key=lambda x: x.get("combined_score", 0),
                reverse=True,
            )
            
            logger.info(f"Reranked {len(documents)} documents")
            return reranked
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return documents


# Global reranker instance
reranker = Reranker()
"""
Retrieval Service - Fetch relevant documents from vector store
"""

import logging
from typing import List, Dict, Any, Optional

from core.vector_store import vector_store
from services.rag_engine.embedder import embedder
from services.rag_engine.reranker import reranker

logger = logging.getLogger(__name__)


class Retriever:
    """
    Handles document retrieval using vector similarity
    """
    
    def __init__(self):
        self.default_top_k = 5
        self.rerank_enabled = True
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for a query text
        """
        return await embedder.get_query_embedding(text)
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        rerank: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents in the vector store
        
        Args:
            query_embedding: Vector of the query
            top_k: Number of results to retrieve
            filter_metadata: Optional metadata filters
            rerank: Whether to apply cross-encoder reranking
        
        Returns:
            List of retrieved documents with scores
        """
        # Retrieve from vector store
        results = await vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k * 2 if rerank else top_k,  # Retrieve extra for reranking
            filter_metadata=filter_metadata,
        )
        
        if not results:
            logger.warning("No documents retrieved from vector store")
            return []
        
        # Apply reranking if enabled
        if rerank and self.rerank_enabled and len(results) > 1:
            results = await reranker.rerank(results, query_embedding)
            results = results[:top_k]  # Take top K after reranking
        
        logger.info(f"Retrieved {len(results)} documents")
        return results
    
    async def search_by_text(
        self,
        query_text: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search using raw text (embeds the text first)
        
        Args:
            query_text: User query string
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
        
        Returns:
            List of retrieved documents
        """
        # Generate embedding for query
        query_embedding = await embedder.get_query_embedding(query_text)
        
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []
        
        # Perform similarity search
        return await self.similarity_search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )
    
    async def search_with_keywords(
        self,
        query_text: str,
        keywords: List[str],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search: Combine vector similarity with keyword matching
        """
        # Get vector search results
        vector_results = await self.search_by_text(query_text, top_k=top_k * 2)
        
        # Boost scores for documents containing keywords
        for result in vector_results:
            text = result.get("text", "").lower()
            keyword_boost = sum(1 for kw in keywords if kw.lower() in text)
            result["similarity_score"] *= (1 + keyword_boost * 0.1)  # 10% boost per keyword
        
        # Re-sort by boosted scores
        vector_results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
        
        return vector_results[:top_k]


# Global retriever instance
retriever = Retriever()
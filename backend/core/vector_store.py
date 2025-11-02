"""
Vector Database Client for RAG Retrieval
Supports ChromaDB (local) and Pinecone (production)
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector database abstraction layer"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.collection_name = "knowledge_base_docs"
    
    async def initialize(self):
        """Initialize ChromaDB client and collection"""
        try:
            self.client = chromadb.Client(ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=settings.CHROMA_PERSIST_DIR,
                anonymized_telemetry=False,
            ))
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            
            logger.info(f"Vector store initialized with collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    async def add_documents(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        documents: List[str],
    ) -> None:
        """
        Add documents to vector store
        
        Args:
            ids: Unique identifiers for each chunk
            embeddings: Vector embeddings (1536-dim for OpenAI)
            metadatas: Metadata (source file, page number, etc.)
            documents: Original text chunks
        """
        if not self.collection:
            await self.initialize()
        
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents,
            )
            logger.info(f"Added {len(ids)} document chunks to vector store")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Vector of the query
            top_k: Number of results to return
            filter_metadata: Metadata filter (e.g., {"source": "policy.pdf"})
        
        Returns:
            List of documents with metadata and scores
        """
        if not self.collection:
            await self.initialize()
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"],
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                })
            
            logger.info(f"Retrieved {len(formatted_results)} documents for query")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    async def delete_document(self, document_id: str) -> None:
        """Delete all chunks associated with a document"""
        if not self.collection:
            await self.initialize()
        
        try:
            # Get all chunks for this document
            # Note: ChromaDB doesn't support direct deletion by metadata filter
            # We need to query and then delete by IDs
            results = self.collection.get(
                where={"document_id": document_id},
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection"""
        if not self.collection:
            await self.initialize()
        
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_chunks": count,
                "persist_directory": settings.CHROMA_PERSIST_DIR,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}


# Global vector store instance
vector_store = VectorStore()
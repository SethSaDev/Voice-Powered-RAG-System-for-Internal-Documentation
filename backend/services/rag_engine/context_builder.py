"""
Context Builder - Formats retrieved documents into LLM prompt context
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds context strings from retrieved documents for LLM consumption
    """
    
    def __init__(self):
        self.max_context_tokens = 3000  # Leave room for prompt and response
        self.token_estimation_factor = 1.3  # Rough estimate: 1 token ≈ 0.75 words
    
    def build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Build a formatted context string from retrieved documents
        
        Args:
            documents: List of retrieved document chunks with metadata
        
        Returns:
            Formatted context string for LLM
        """
        if not documents:
            return "No relevant documents found in the knowledge base."
        
        context_parts = []
        total_chars = 0
        
        for i, doc in enumerate(documents, 1):
            text = doc.get("text", "").strip()
            metadata = doc.get("metadata", {})
            score = doc.get("similarity_score", 0)
            
            if not text:
                continue
            
            # Format with source attribution
            source = metadata.get("source", metadata.get("filename", "Unknown source"))
            page = metadata.get("page", "")
            
            header = f"[Source: {source}"
            if page:
                header += f", Page: {page}"
            header += f", Relevance: {score:.2f}]"
            
            context_part = f"{header}\n{text}\n"
            
            # Check token budget
            estimated_tokens = len(context_part) / self.token_estimation_factor
            if total_chars + len(context_part) > self.max_context_tokens * self.token_estimation_factor:
                # Truncate to fit budget
                remaining_chars = int(self.max_context_tokens * self.token_estimation_factor - total_chars)
                if remaining_chars > 100:
                    context_part = context_part[:remaining_chars] + "...\n"
                else:
                    break
            
            context_parts.append(context_part)
            total_chars += len(context_part)
        
        if not context_parts:
            return "No relevant content could be extracted from the retrieved documents."
        
        return "\n---\n".join(context_parts)
    
    def build_context_with_highlights(
        self,
        documents: List[Dict[str, Any]],
        query: str,
    ) -> str:
        """
        Build context with highlighted relevant passages
        """
        context = self.build_context(documents)
        
        # Simple highlighting of query terms (optional)
        if query:
            query_terms = set(query.lower().split())
            highlighted_context = context
            
            for term in query_terms:
                if len(term) > 3:  # Only highlight meaningful terms
                    highlighted_context = highlighted_context.replace(
                        term,
                        f"**{term}**",
                    )
            
            return highlighted_context
        
        return context


# Global context builder instance
context_builder = ContextBuilder()
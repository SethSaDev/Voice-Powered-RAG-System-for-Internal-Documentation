from typing import List, Dict, Any

class ContextBuilder:
    """Build context from retrieved documents"""
    
    def build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format documents into context string"""
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[Source {i}]\n{doc.get('text', '')}")
        
        return "\n\n---\n\n".join(context_parts)

context_builder = ContextBuilder()

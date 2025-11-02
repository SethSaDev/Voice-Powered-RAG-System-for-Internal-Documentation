"""
Prompt Templates for RAG-based Q&A
Centralized prompt management for consistent responses
"""

from typing import Dict, Any


class PromptTemplates:
    """
    Manages prompt templates for different use cases
    """
    
    def get_system_prompt(self) -> str:
        """
        System prompt that defines the AI's behavior
        """
        return """You are an intelligent knowledge base assistant for an enterprise. Your role is to help employees find information from company documentation, policies, and internal resources.

Guidelines:
1. **Be accurate**: Base your answers STRICTLY on the provided context documents
2. **Be helpful**: If information isn't in the context, say "I don't have that information in my knowledge base" rather than guessing
3. **Cite sources**: When referencing information, mention the source document (e.g., "According to the employee handbook...")
4. **Be concise**: Provide clear, direct answers without unnecessary fluff
5. **Be professional**: Maintain a helpful, respectful tone appropriate for a workplace
6. **Handle follow-ups**: If the user asks for clarification, provide additional details from the context

If the context doesn't contain relevant information for the query, politely state that you cannot find the answer and suggest they consult HR or their manager for specific policies.

Remember: You are an AI assistant, not a human. Be transparent about your capabilities and limitations."""
    
    def format_user_message(self, query: str, context: str) -> str:
        """
        Format user message with context
        """
        if not context or context == "No relevant documents found in the knowledge base.":
            return f"""Question: {query}

Context: No relevant documents were found in the knowledge base. Please answer based on your general knowledge, but clearly indicate that this information may not be specific to the company's policies.

Please provide a helpful response:"""
        
        return f"""Context from company knowledge base:
{context}

Question: {query}

Please answer the question based STRICTLY on the context provided above. If the answer cannot be found in the context, say so clearly."""
    
    def get_followup_prompt(self, query: str, response: str, context: str) -> str:
        """
        Generate follow-up question suggestions
        """
        return f"""Based on this conversation:

User Query: {query}
AI Response: {response}
Context Used: {context[:300]}...

Suggest 3 relevant follow-up questions the user might want to ask next.
Each question should be on a new line starting with a dash (-).
Focus on related topics that might be covered in the context but not yet explored.

Example:
- What are the specific steps to implement this?
- Are there any exceptions to this policy?
- Who should I contact for more details?"""
    
    def get_summarization_prompt(self, documents: list) -> str:
        """
        Summarize multiple documents for batch processing
        """
        docs_text = "\n\n".join([doc.get("text", "")[:500] for doc in documents[:3]])
        
        return f"""Please provide a concise summary of the following documents:

{docs_text}

Summary (3-5 sentences):"""
    
    def get_query_rewrite_prompt(self, original_query: str, history: list) -> str:
        """
        Rewrite ambiguous queries using conversation history
        """
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-3:]])
        
        return f"""Given the conversation history and the current user query, rewrite the current query to be self-contained and unambiguous.

Conversation History:
{history_text}

Current Query: {original_query}

Rewritten Query:"""
    
    def get_intent_classification_prompt(self, query: str) -> Dict[str, Any]:
        """
        Classify user intent for routing
        """
        # This would return a classification schema
        # For now, used by intent classifier service
        return {
            "intents": ["factual_question", "policy_inquiry", "procedure_request", "greeting", "feedback"],
            "query": query,
        }


# Global prompt templates instance
prompt_templates = PromptTemplates()
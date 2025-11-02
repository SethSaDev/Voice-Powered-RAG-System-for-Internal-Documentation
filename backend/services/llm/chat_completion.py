"""
LLM Chat Completion Service - Handles GPT-4/GPT-3.5 interactions with RAG context
"""

import logging
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from services.llm.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


class LLMChat:
    """
    Orchestrates LLM interactions with context from RAG pipeline
    """
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.temperature = 0.7
        self.max_tokens = 1000
        self.prompt_templates = PromptTemplates()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def generate_response(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate a response using the LLM with RAG context
        
        Args:
            query: User's question
            context: Retrieved document context
            conversation_history: Previous messages in the conversation
            system_prompt: Custom system prompt (overrides default)
            temperature: Sampling temperature (0-2)
        
        Returns:
            Generated response text
        """
        try:
            # Build messages array
            messages = []
            
            # System prompt
            system_content = system_prompt or self.prompt_templates.get_system_prompt()
            messages.append({"role": "system", "content": system_content})
            
            # Add conversation history (last 5 messages for context)
            if conversation_history:
                messages.extend(conversation_history[-5:])
            
            # Add current query with context
            user_message = self.prompt_templates.format_user_message(query, context)
            messages.append({"role": "user", "content": user_message})
            
            # Log prompt (truncated for debugging)
            logger.debug(f"LLM prompt length: {len(json.dumps(messages))} chars")
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=self.max_tokens,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )
            
            result = response.choices[0].message.content
            logger.info(f"LLM response generated: {len(result)} chars")
            
            return result.strip()
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
    
    async def generate_streaming_response(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response (token by token)
        """
        try:
            messages = [
                {"role": "system", "content": self.prompt_templates.get_system_prompt()},
            ]
            
            if conversation_history:
                messages.extend(conversation_history[-5:])
            
            user_message = self.prompt_templates.format_user_message(query, context)
            messages.append({"role": "user", "content": user_message})
            
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming LLM generation failed: {e}")
            yield "I apologize, but I'm experiencing technical difficulties. Please try again."
    
    async def generate_followup_suggestions(
        self,
        query: str,
        response: str,
        context: str,
    ) -> List[str]:
        """
        Generate follow-up question suggestions based on the conversation
        """
        prompt = self.prompt_templates.get_followup_prompt(query, response, context)
        
        try:
            result = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for follow-ups
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that suggests relevant follow-up questions."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=150,
            )
            
            suggestions_text = result.choices[0].message.content
            suggestions = [s.strip("-• ").strip() for s in suggestions_text.split("\n") if s.strip()]
            
            return suggestions[:3]  # Return top 3
            
        except Exception as e:
            logger.error(f"Follow-up generation failed: {e}")
            return ["What else would you like to know?", "Can you clarify your question?", "Would you like more details on this topic?"]
    
    async def evaluate_response_quality(
        self,
        query: str,
        response: str,
        context: str,
    ) -> Dict[str, Any]:
        """
        Evaluate the quality of the generated response
        """
        prompt = f"""
        Evaluate the quality of this AI response based on:
        1. Relevance to the query
        2. Accuracy based on provided context
        3. Completeness
        4. Clarity
        
        Query: {query}
        Context: {context[:500]}...
        Response: {response}
        
        Return JSON with scores (0-10) and brief reasoning.
        """
        
        try:
            result = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a response quality evaluator. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=200,
            )
            
            evaluation = json.loads(result.choices[0].message.content)
            return evaluation
            
        except Exception as e:
            logger.error(f"Response evaluation failed: {e}")
            return {
                "relevance": 7,
                "accuracy": 7,
                "completeness": 7,
                "clarity": 8,
                "overall": 7.25,
                "reasoning": "Automatic evaluation unavailable",
            }


# Global LLM chat instance
llm_chat = LLMChat()
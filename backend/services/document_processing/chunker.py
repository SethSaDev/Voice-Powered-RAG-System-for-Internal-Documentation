"""
Text Chunking - Splits documents into manageable pieces for embedding
"""

import logging
from typing import List
import re

logger = logging.getLogger(__name__)


async def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
    separator: str = "\n\n",
) -> List[str]:
    """
    Split text into overlapping chunks for better context retention
    
    Args:
        text: Input text to chunk
        chunk_size: Target size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        separator: Separator for natural breaks (paragraphs, sentences)
    
    Returns:
        List of text chunks
    """
    if not text or len(text) < chunk_size:
        return [text] if text else []
    
    chunks = []
    
    # Try to split by paragraphs first
    paragraphs = text.split(separator)
    
    current_chunk = ""
    current_size = 0
    
    for para in paragraphs:
        para_size = len(para)
        
        # If paragraph is too large, split it further
        if para_size > chunk_size:
            # Split large paragraph into sentences
            sentences = _split_into_sentences(para)
            
            for sentence in sentences:
                sentence_size = len(sentence)
                
                if current_size + sentence_size <= chunk_size:
                    if current_chunk:
                        current_chunk += " "
                    current_chunk += sentence
                    current_size += sentence_size + 1
                else:
                    # Save current chunk
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    
                    # Start new chunk with overlap
                    overlap_text = _get_overlap_text(current_chunk, overlap)
                    current_chunk = overlap_text + " " + sentence if overlap_text else sentence
                    current_size = len(current_chunk)
        
        else:
            # Normal paragraph fits or needs chunking
            if current_size + para_size + 2 <= chunk_size:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += para
                current_size += para_size + 2
            else:
                # Save current chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk
                overlap_text = _get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + "\n\n" + para if overlap_text else para
                current_size = len(current_chunk)
    
    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Filter out very short chunks (noise)
    chunks = [chunk for chunk in chunks if len(chunk) > 50]
    
    logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")
    
    return chunks


def _split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences for finer-grained chunking
    """
    # Simple sentence splitting (can be improved with NLP)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _get_overlap_text(chunk: str, overlap_chars: int) -> str:
    """
    Get overlapping text from the end of a chunk for context preservation
    """
    if not chunk or len(chunk) <= overlap_chars:
        return ""
    
    # Find the last sentence boundary within overlap range
    overlap_text = chunk[-overlap_chars:]
    
    # Try to start at a word boundary
    first_space = overlap_text.find(" ")
    if first_space > 0:
        overlap_text = overlap_text[first_space:].strip()
    
    return overlap_text
"""
Document Text Extraction - Supports PDF, DOCX, TXT, MD, HTML
"""

import logging
from pathlib import Path
from typing import Optional
import aiofiles

logger = logging.getLogger(__name__)


async def extract_text_from_document(file_path: str, file_type: str) -> Optional[str]:
    """
    Extract text from various document formats
    
    Args:
        file_path: Path to the document file
        file_type: Type of document (pdf, docx, txt, md, html)
    
    Returns:
        Extracted text or None if extraction failed
    """
    path = Path(file_path)
    
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return None
    
    try:
        if file_type == "txt" or file_type == "md":
            return await _extract_text_txt(path)
        elif file_type == "pdf":
            return await _extract_text_pdf(path)
        elif file_type == "docx":
            return await _extract_text_docx(path)
        elif file_type == "html":
            return await _extract_text_html(path)
        else:
            logger.error(f"Unsupported file type: {file_type}")
            return None
            
    except Exception as e:
        logger.error(f"Text extraction failed for {file_path}: {e}")
        return None


async def _extract_text_txt(file_path: Path) -> str:
    """Extract text from plain text files"""
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        text = await f.read()
    return text


async def _extract_text_pdf(file_path: Path) -> str:
    """Extract text from PDF files"""
    try:
        import pypdf
        
        text_parts = []
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
        
    except ImportError:
        logger.error("pypdf not installed")
        return ""
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return ""


async def _extract_text_docx(file_path: Path) -> str:
    """Extract text from DOCX files"""
    try:
        import docx
        
        doc = docx.Document(file_path)
        text_parts = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
        return "\n\n".join(text_parts)
        
    except ImportError:
        logger.error("python-docx not installed")
        return ""
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        return ""


async def _extract_text_html(file_path: Path) -> str:
    """Extract text from HTML files"""
    try:
        from bs4 import BeautifulSoup
        
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            html = await f.read()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
        
    except ImportError:
        logger.error("beautifulsoup4 not installed")
        return ""
    except Exception as e:
        logger.error(f"HTML extraction error: {e}")
        return ""
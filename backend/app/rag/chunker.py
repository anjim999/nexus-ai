"""
========================================
Document Chunker
========================================
Split documents into chunks for indexing
"""

import os
from typing import List, Dict, Any
import asyncio

from app.config import settings


async def chunk_document(file_path: str) -> List[Dict[str, Any]]:
    """
    Split a document into chunks
    
    Args:
        file_path: Path to the document
        
    Returns:
        List of chunks with text and metadata
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        return await chunk_pdf(file_path)
    elif ext == ".txt":
        return await chunk_text(file_path)
    elif ext == ".csv":
        return await chunk_csv(file_path)
    elif ext == ".json":
        return await chunk_json(file_path)
    elif ext == ".docx":
        return await chunk_docx(file_path)
    else:
        # Try as plain text
        return await chunk_text(file_path)


async def chunk_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Extract and chunk PDF content"""
    from pypdf import PdfReader
    
    chunks = []
    
    try:
        reader = await asyncio.to_thread(PdfReader, file_path)
        
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            
            if text and text.strip():
                # Split page into chunks
                page_chunks = split_text(
                    text,
                    chunk_size=settings.CHUNK_SIZE,
                    overlap=settings.CHUNK_OVERLAP
                )
                
                for chunk in page_chunks:
                    chunks.append({
                        "text": chunk,
                        "page": page_num,
                        "type": "pdf"
                    })
    except Exception as e:
        print(f"PDF extraction error: {e}")
    
    return chunks


async def chunk_text(file_path: str) -> List[Dict[str, Any]]:
    """Extract and chunk plain text"""
    chunks = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        text_chunks = split_text(
            text,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )
        
        for i, chunk in enumerate(text_chunks):
            chunks.append({
                "text": chunk,
                "page": None,
                "section": i + 1,
                "type": "text"
            })
    except Exception as e:
        print(f"Text extraction error: {e}")
    
    return chunks


async def chunk_csv(file_path: str) -> List[Dict[str, Any]]:
    """Extract and chunk CSV content"""
    import pandas as pd
    
    chunks = []
    
    try:
        df = await asyncio.to_thread(pd.read_csv, file_path)
        
        # Convert rows to text
        for i, row in df.iterrows():
            row_text = " | ".join([
                f"{col}: {val}" 
                for col, val in row.items() 
                if pd.notna(val)
            ])
            
            if row_text.strip():
                chunks.append({
                    "text": row_text,
                    "page": None,
                    "row": i + 1,
                    "type": "csv"
                })
        
        # Also add a summary chunk
        summary = f"CSV with {len(df)} rows and columns: {', '.join(df.columns)}"
        chunks.insert(0, {
            "text": summary,
            "page": None,
            "type": "csv_summary"
        })
        
    except Exception as e:
        print(f"CSV extraction error: {e}")
    
    return chunks


async def chunk_json(file_path: str) -> List[Dict[str, Any]]:
    """Extract and chunk JSON content"""
    import json
    
    chunks = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert JSON to text representation
        json_text = json.dumps(data, indent=2)
        
        text_chunks = split_text(
            json_text,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )
        
        for i, chunk in enumerate(text_chunks):
            chunks.append({
                "text": chunk,
                "page": None,
                "section": i + 1,
                "type": "json"
            })
    except Exception as e:
        print(f"JSON extraction error: {e}")
    
    return chunks


async def chunk_docx(file_path: str) -> List[Dict[str, Any]]:
    """Extract and chunk Word document"""
    from docx import Document
    
    chunks = []
    
    try:
        doc = await asyncio.to_thread(Document, file_path)
        
        full_text = "\n".join([
            para.text
            for para in doc.paragraphs
            if para.text.strip()
        ])
        
        text_chunks = split_text(
            full_text,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )
        
        for i, chunk in enumerate(text_chunks):
            chunks.append({
                "text": chunk,
                "page": None,
                "section": i + 1,
                "type": "docx"
            })
    except Exception as e:
        print(f"DOCX extraction error: {e}")
    
    return chunks


def split_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Text to split
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at a sentence or paragraph
        if end < len(text):
            # Look for paragraph break
            para_break = text.rfind('\n\n', start, end)
            if para_break > start:
                end = para_break
            else:
                # Look for sentence break
                for sep in ['. ', '! ', '? ', '\n']:
                    sent_break = text.rfind(sep, start, end)
                    if sent_break > start:
                        end = sent_break + len(sep)
                        break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start with overlap
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

# Document Chunker
# Split documents into chunks for indexing

import os
import csv
from typing import List, Dict, Any
import asyncio

from app.config import settings


async def chunk_document(file_path: str) -> List[Dict[str, Any]]:
    # Split a document into chunks
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
    # Extract and chunk PDF content using LangChain PyPDFLoader
    from langchain_community.document_loaders import PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    chunks = []
    try:
        loader = PyPDFLoader(file_path)
        docs = await asyncio.to_thread(loader.load)
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
        split_docs = splitter.split_documents(docs)
        
        for doc in split_docs:
            chunks.append({
                "text": doc.page_content,
                "page": doc.metadata.get("page", 0) + 1,  # 0-indexed to 1-indexed
                "type": "pdf"
            })
    except Exception as e:
        print(f"PDF extraction error: {e}")
    
    return chunks


async def chunk_text(file_path: str) -> List[Dict[str, Any]]:
    # Extract and chunk plain text using LangChain TextLoader
    from langchain_community.document_loaders import TextLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    chunks = []
    try:
        loader = TextLoader(file_path, encoding='utf-8')
        docs = await asyncio.to_thread(loader.load)
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
        split_docs = splitter.split_documents(docs)
        
        for i, doc in enumerate(split_docs):
            chunks.append({
                "text": doc.page_content,
                "page": None,
                "section": i + 1,
                "type": "text"
            })
    except Exception as e:
        print(f"Text extraction error: {e}")
    
    return chunks


async def chunk_csv(file_path: str) -> List[Dict[str, Any]]:
    # Extract and chunk CSV using LangChain CSVLoader
    from langchain_community.document_loaders import CSVLoader
    
    chunks = []
    try:
        loader = CSVLoader(file_path)
        docs = await asyncio.to_thread(loader.load)
        
        for i, doc in enumerate(docs):
            chunks.append({
                "text": doc.page_content,
                "page": None,
                "row": doc.metadata.get("row", i) + 1,
                "type": "csv"
            })
    except Exception as e:
        print(f"CSV extraction error: {e}")
    
    return chunks


async def chunk_json(file_path: str) -> List[Dict[str, Any]]:
    # Extract and chunk JSON using LangChain TextLoader
    from langchain_community.document_loaders import TextLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    chunks = []
    try:
        loader = TextLoader(file_path, encoding='utf-8')
        docs = await asyncio.to_thread(loader.load)
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
        split_docs = splitter.split_documents(docs)
        
        for i, doc in enumerate(split_docs):
            chunks.append({
                "text": doc.page_content,
                "page": None,
                "section": i + 1,
                "type": "json"
            })
    except Exception as e:
        print(f"JSON extraction error: {e}")
    
    return chunks


async def chunk_docx(file_path: str) -> List[Dict[str, Any]]:
    # Extract and chunk Word document using LangChain Docx2txtLoader
    from langchain_community.document_loaders import Docx2txtLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    chunks = []
    try:
        loader = Docx2txtLoader(file_path)
        docs = await asyncio.to_thread(loader.load)
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
        split_docs = splitter.split_documents(docs)
        
        for i, doc in enumerate(split_docs):
            chunks.append({
                "text": doc.page_content,
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
    # Split text using LangChain's RecursiveCharacterTextSplitter
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    return [doc.page_content for doc in splitter.create_documents([text])]

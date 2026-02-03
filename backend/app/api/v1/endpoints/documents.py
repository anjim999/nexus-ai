"""
========================================
Document Endpoints
========================================
Upload, manage, and search documents
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import os
import uuid
import aiofiles

from app.config import settings
from app.dependencies import get_vector_store
from app.rag.vectorstore import VectorStore

router = APIRouter()


# ========================================
# Schemas
# ========================================
class DocumentMetadata(BaseModel):
    """Document metadata"""
    id: str
    filename: str
    file_type: str
    size_bytes: int
    uploaded_at: datetime
    chunk_count: int
    status: str = "processed"


class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    id: str
    filename: str
    message: str
    chunk_count: int
    processing_time_ms: int


class DocumentSearchRequest(BaseModel):
    """Search within documents"""
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    file_filter: Optional[List[str]] = Field(default=None, description="Filter by filename")


class DocumentSearchResult(BaseModel):
    """Single search result"""
    content: str
    source: str
    page: Optional[int] = None
    relevance_score: float


class DocumentListResponse(BaseModel):
    """List of all documents"""
    documents: List[DocumentMetadata]
    total_count: int


# ========================================
# Endpoints
# ========================================
@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = Form(default=None),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Upload a document for RAG processing.
    
    Supported formats:
    - PDF (.pdf)
    - Text (.txt)
    - CSV (.csv)
    - Word (.docx)
    - JSON (.json)
    
    The document will be:
    1. Saved to storage
    2. Split into chunks
    3. Converted to embeddings
    4. Indexed for search
    """
    import time
    start_time = time.time()
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' not supported. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Validate file size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # Generate unique ID and save file
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{file.filename}")
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Process and index document
    try:
        chunk_count = await vector_store.add_document(
            file_path=file_path,
            doc_id=doc_id,
            metadata={
                "filename": file.filename,
                "description": description,
                "file_type": file_ext,
                "size_bytes": len(content)
            }
        )
    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
    
    processing_time = int((time.time() - start_time) * 1000)
    
    return DocumentUploadResponse(
        id=doc_id,
        filename=file.filename,
        message="Document uploaded and indexed successfully",
        chunk_count=chunk_count,
        processing_time_ms=processing_time
    )


@router.post("/upload/multiple", response_model=List[DocumentUploadResponse])
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Upload multiple documents at once.
    """
    results = []
    
    for file in files:
        try:
            # Reuse single upload logic
            result = await upload_document(file=file, vector_store=vector_store)
            results.append(result)
        except HTTPException as e:
            results.append({
                "filename": file.filename,
                "error": e.detail,
                "status": "failed"
            })
    
    return results


@router.post("/search", response_model=List[DocumentSearchResult])
async def search_documents(
    request: DocumentSearchRequest,
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Search across all uploaded documents using semantic search.
    
    Returns the most relevant chunks matching your query.
    """
    results = await vector_store.search(
        query=request.query,
        top_k=request.top_k,
        file_filter=request.file_filter
    )
    
    return [
        DocumentSearchResult(
            content=r["content"],
            source=r["source"],
            page=r.get("page"),
            relevance_score=r["score"]
        )
        for r in results
    ]


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    List all uploaded documents.
    """
    documents = await vector_store.list_documents()
    
    return DocumentListResponse(
        documents=documents,
        total_count=len(documents)
    )


@router.get("/{doc_id}", response_model=DocumentMetadata)
async def get_document(
    doc_id: str,
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Get metadata for a specific document.
    """
    doc = await vector_store.get_document(doc_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return doc


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Delete a document and remove from index.
    """
    success = await vector_store.delete_document(doc_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"status": "deleted", "doc_id": doc_id}


@router.post("/reindex")
async def reindex_all_documents(
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Reindex all documents. Useful after embedding model changes.
    """
    count = await vector_store.reindex_all()
    
    return {
        "status": "reindexed",
        "document_count": count
    }

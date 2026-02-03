"""
========================================
Vector Store
========================================
FAISS-based vector database for RAG
"""

import os
import json
import pickle
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

import faiss
import numpy as np

from app.config import settings
from app.core.exceptions import RAGException


class VectorStore:
    """
    FAISS Vector Store for semantic search
    
    Features:
    - Document indexing
    - Semantic search
    - Metadata filtering
    - Persistence
    """
    
    def __init__(self, path: str = None):
        self.path = path or settings.VECTOR_STORE_PATH
        self.dimension = 768  # Gemini embedding dimension
        
        # Initialize FAISS index
        self.index: Optional[faiss.IndexFlatIP] = None
        
        # Document storage
        self.documents: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        
        # Load existing index if present
        self._load()
    
    # ========================================
    # Index Management
    # ========================================
    def _create_index(self):
        """Create a new FAISS index"""
        # Using Inner Product (cosine similarity after normalization)
        self.index = faiss.IndexFlatIP(self.dimension)
    
    def _load(self):
        """Load index from disk"""
        index_path = os.path.join(self.path, "faiss.index")
        docs_path = os.path.join(self.path, "documents.pkl")
        meta_path = os.path.join(self.path, "metadata.json")
        
        if os.path.exists(index_path) and os.path.exists(docs_path):
            try:
                self.index = faiss.read_index(index_path)
                with open(docs_path, 'rb') as f:
                    self.documents = pickle.load(f)
                if os.path.exists(meta_path):
                    with open(meta_path, 'r') as f:
                        self.metadata = json.load(f)
            except Exception as e:
                print(f"Error loading index: {e}")
                self._create_index()
        else:
            self._create_index()
    
    def _save(self):
        """Save index to disk"""
        os.makedirs(self.path, exist_ok=True)
        
        index_path = os.path.join(self.path, "faiss.index")
        docs_path = os.path.join(self.path, "documents.pkl")
        meta_path = os.path.join(self.path, "metadata.json")
        
        faiss.write_index(self.index, index_path)
        with open(docs_path, 'wb') as f:
            pickle.dump(self.documents, f)
        with open(meta_path, 'w') as f:
            json.dump(self.metadata, f)
    
    # ========================================
    # Document Operations
    # ========================================
    async def add_document(
        self,
        file_path: str,
        doc_id: str,
        metadata: Dict[str, Any] = None
    ) -> int:
        """
        Add a document to the vector store
        
        Args:
            file_path: Path to the document file
            doc_id: Unique document identifier
            metadata: Additional metadata
            
        Returns:
            Number of chunks indexed
        """
        from app.rag.chunker import chunk_document
        from app.rag.embeddings import get_embeddings
        
        # Chunk the document
        chunks = await chunk_document(file_path)
        
        if not chunks:
            raise RAGException(f"No content extracted from {file_path}")
        
        # Get embeddings for all chunks
        texts = [c["text"] for c in chunks]
        embeddings = await get_embeddings(texts)
        
        # Normalize for cosine similarity
        embeddings_np = np.array(embeddings).astype('float32')
        faiss.normalize_L2(embeddings_np)
        
        # Add to index
        start_idx = len(self.documents)
        self.index.add(embeddings_np)
        
        # Store documents with metadata
        for i, chunk in enumerate(chunks):
            doc_entry = {
                "id": f"{doc_id}_{i}",
                "doc_id": doc_id,
                "text": chunk["text"],
                "page": chunk.get("page"),
                "source": os.path.basename(file_path),
                "metadata": metadata or {},
                "indexed_at": datetime.now().isoformat()
            }
            self.documents.append(doc_entry)
        
        # Update metadata
        self.metadata[doc_id] = {
            "filename": os.path.basename(file_path),
            "file_type": os.path.splitext(file_path)[1],
            "chunk_count": len(chunks),
            "indexed_at": datetime.now().isoformat(),
            **( metadata or {})
        }
        
        # Persist
        self._save()
        
        return len(chunks)
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        file_filter: Optional[List[str]] = None,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            top_k: Number of results
            file_filter: Filter by filename
            threshold: Minimum similarity score
            
        Returns:
            List of matching documents with scores
        """
        from app.rag.embeddings import get_query_embedding
        
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Get query embedding
        query_embedding = await get_query_embedding(query)
        query_np = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_np)
        
        # Search
        # Get more results for filtering
        search_k = min(top_k * 3, self.index.ntotal)
        scores, indices = self.index.search(query_np, search_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            
            if score < threshold:
                continue
            
            doc = self.documents[idx]
            
            # Apply file filter
            if file_filter:
                if doc["source"] not in file_filter:
                    continue
            
            results.append({
                "content": doc["text"],
                "source": doc["source"],
                "page": doc.get("page"),
                "doc_id": doc["doc_id"],
                "score": float(score),
                "metadata": doc.get("metadata", {})
            })
            
            if len(results) >= top_k:
                break
        
        return results
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the store
        
        Note: FAISS doesn't support deletion, so we rebuild the index
        """
        # Find documents to keep
        docs_to_keep = []
        indices_to_keep = []
        
        for i, doc in enumerate(self.documents):
            if doc["doc_id"] != doc_id:
                docs_to_keep.append(doc)
                indices_to_keep.append(i)
        
        if len(docs_to_keep) == len(self.documents):
            return False  # Document not found
        
        # Rebuild index with remaining documents
        if indices_to_keep:
            from app.rag.embeddings import get_embeddings
            
            texts = [d["text"] for d in docs_to_keep]
            embeddings = await get_embeddings(texts)
            
            embeddings_np = np.array(embeddings).astype('float32')
            faiss.normalize_L2(embeddings_np)
            
            self._create_index()
            self.index.add(embeddings_np)
        else:
            self._create_index()
        
        self.documents = docs_to_keep
        
        # Remove from metadata
        if doc_id in self.metadata:
            del self.metadata[doc_id]
        
        self._save()
        return True
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all indexed documents"""
        docs = []
        for doc_id, meta in self.metadata.items():
            docs.append({
                "id": doc_id,
                "filename": meta.get("filename"),
                "file_type": meta.get("file_type"),
                "chunk_count": meta.get("chunk_count", 0),
                "size_bytes": meta.get("size_bytes", 0),
                "uploaded_at": meta.get("indexed_at"),
                "status": "indexed"
            })
        return docs
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata"""
        if doc_id in self.metadata:
            meta = self.metadata[doc_id]
            return {
                "id": doc_id,
                "filename": meta.get("filename"),
                "file_type": meta.get("file_type"),
                "chunk_count": meta.get("chunk_count", 0),
                "size_bytes": meta.get("size_bytes", 0),
                "uploaded_at": meta.get("indexed_at"),
                "status": "indexed"
            }
        return None
    
    async def reindex_all(self) -> int:
        """Reindex all documents"""
        # Would need to re-read all documents from disk
        # For now, return current count
        return len(self.metadata)
    
    # ========================================
    # Statistics
    # ========================================
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            "total_documents": len(self.metadata),
            "total_chunks": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "dimension": self.dimension
        }


# ========================================
# Global Instance
# ========================================
_vector_store: Optional[VectorStore] = None


async def init_vector_store():
    """Initialize the global vector store"""
    global _vector_store
    os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
    _vector_store = VectorStore()


def get_vector_store() -> VectorStore:
    """Get the global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

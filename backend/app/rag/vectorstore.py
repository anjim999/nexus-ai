# Vector Store
# Pinecone-based cloud vector database for RAG (Retrieval-Augmented Generation) using LangChain

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from langchain_pinecone import PineconeVectorStore
from app.rag.embeddings import _embeddings_client

from app.config import settings
from app.core.exceptions import RAGException


class VectorStore:
    # LangChain Pinecone Vector Store wrapper
    # Features: Document indexing, Semantic search, Metadata filtering, Cloud Persistence
    
    def __init__(self, path: str = None):
        self.path = path or settings.VECTOR_STORE_PATH
        self.dimension = 3072  # Gemini embedding dimension
        self.store = None
        
        # Check settings
        if not settings.PINECONE_API_KEY or not settings.PINECONE_INDEX_NAME:
            import logging
            logging.getLogger("app").warning(
                "Pinecone is not configured. Please set PINECONE_API_KEY and "
                "PINECONE_INDEX_NAME in your environment variables for RAG features."
            )
        else:
            # Initialize LangChain Pinecone client wrapper
            try:
                self.store = PineconeVectorStore(
                    index_name=settings.PINECONE_INDEX_NAME,
                    embedding=_embeddings_client,
                    pinecone_api_key=settings.PINECONE_API_KEY
                )
            except Exception as e:
                import logging
                logging.getLogger("app").warning(
                    f"Failed to initialize LangChain Pinecone Store: {str(e)}"
                )
                
    def _check_configured(self):
        if not self.store:
            raise RAGException(
                "Pinecone is not configured. Please set PINECONE_API_KEY and "
                "PINECONE_INDEX_NAME in your environment variables."
            )
            
        # Document metadata catalog (stored locally for rapid listing)
        self.metadata: Dict[str, Any] = {}
        
        # Load existing metadata catalog if present
        self._load()
    
    def _load(self):
        # Load local document metadata catalog from disk
        meta_path = os.path.join(self.path, "metadata.json")
        
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"Error loading metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _save(self):
        # Save local document metadata catalog to disk
        os.makedirs(self.path, exist_ok=True)
        meta_path = os.path.join(self.path, "metadata.json")
        
        try:
            with open(meta_path, 'w') as f:
                json.dump(self.metadata, f)
        except Exception as e:
            print(f"Error saving metadata: {e}")
            raise RAGException(f"Failed to persist metadata catalog: {str(e)}")
    
    # Document Operations - Add, Search, and Delete documents from the store
    async def add_document(
        self,
        file_path: str,
        doc_id: str,
        metadata: Dict[str, Any] = None
    ) -> int:
        self._check_configured()
        # Add a document to the vector store
        # Returns number of chunks indexed
        from app.rag.chunker import chunk_document
        from langchain_core.documents import Document
        
        # Chunk the document using chunk_document (which uses RecursiveCharacterTextSplitter)
        chunks = await chunk_document(file_path)
        
        if not chunks:
            raise RAGException(f"No content extracted from {file_path}")
            
        # Convert text chunks to LangChain Document objects
        documents_to_add = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk["text"],
                metadata={
                    "page": chunk.get("page") or 0,
                    "source": os.path.basename(file_path),
                    "doc_id": doc_id,
                    "chunk_index": i
                }
            )
            documents_to_add.append(doc)
            
        try:
            # Add documents using LangChain PineconeVectorStore
            # It handles embeddings generation and upsertion in chunks
            await asyncio.to_thread(
                self.store.add_documents,
                documents_to_add
            )
        except Exception as e:
            raise RAGException(f"Failed to add documents using LangChain: {str(e)}")
        
        # Update local catalog metadata
        self.metadata[doc_id] = {
            "filename": os.path.basename(file_path),
            "file_type": os.path.splitext(file_path)[1],
            "chunk_count": len(chunks),
            "indexed_at": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        # Persist catalog changes locally
        self._save()
        
        return len(chunks)
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        file_filter: Optional[List[str]] = None,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        self._check_configured()
        # Search for similar documents in Pinecone using LangChain
        # Returns list of matching documents with scores
        
        # Construct filter query if list of filenames is provided
        pinecone_filter = None
        if file_filter:
            pinecone_filter = {"source": {"$in": file_filter}}
            
        try:
            # Query Pinecone using LangChain's similarity search with score
            # similarity_search_with_relevance_scores returns tuples of (Document, score)
            matches = await asyncio.to_thread(
                self.store.similarity_search_with_relevance_scores,
                query,
                k=top_k,
                filter=pinecone_filter
            )
        except Exception as e:
            raise RAGException(f"LangChain Pinecone search failed: {str(e)}")
            
        results = []
        for doc, score in matches:
            # Filter out poor matches using threshold
            if score < threshold:
                continue
                
            results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", ""),
                "page": doc.metadata.get("page"),
                "doc_id": doc.metadata.get("doc_id", ""),
                "score": float(score),
                "metadata": doc.metadata
            })
            
        return results
    
    async def delete_document(self, doc_id: str) -> bool:
        self._check_configured()
        # Delete document vectors from Pinecone using metadata filter
        if doc_id not in self.metadata:
            return False  # Document not found in our catalog
            
        try:
            # LangChain PineconeVectorStore uses raw client to delete by filter
            await asyncio.to_thread(
                self.store.delete,
                filter={"doc_id": doc_id}
            )
        except Exception as e:
            raise RAGException(f"Failed to delete vectors using LangChain: {str(e)}")
            
        # Remove from local metadata catalog
        del self.metadata[doc_id]
        self._save()
        return True
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        # List all indexed documents from the metadata catalog
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
        # Get document metadata from the catalog
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
        return len(self.metadata)
    
    def get_stats(self) -> Dict[str, Any]:
        # Get vector store statistics from local metadata and Pinecone index
        try:
            # We access the raw index object inside PineconeVectorStore
            stats = self.store._index.describe_index_stats()
            total_chunks = stats.total_vector_count
        except Exception:
            total_chunks = 0
            
        return {
            "total_documents": len(self.metadata),
            "total_chunks": total_chunks,
            "index_size": total_chunks,
            "dimension": self.dimension
        }


# Global Instance management for the VectorStore across the app
_vector_store: Optional[VectorStore] = None


async def init_vector_store():
    # Initialize the global vector store
    global _vector_store
    os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
    _vector_store = VectorStore()


def get_vector_store() -> VectorStore:
    # Get the global vector store instance
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

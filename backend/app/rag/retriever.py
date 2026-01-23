"""
========================================
Retriever
========================================
High-level retrieval interface
"""

from typing import List, Dict, Any, Optional

from app.rag.vectorstore import get_vector_store
from app.rag.embeddings import get_query_embedding


class Retriever:
    """
    High-level document retriever
    
    Features:
    - Semantic search
    - Metadata filtering
    - Result re-ranking
    - Context formatting
    """
    
    def __init__(self):
        self.vector_store = get_vector_store()
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        file_filter: Optional[List[str]] = None,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            top_k: Number of results
            file_filter: Filter by filename
            min_score: Minimum relevance score
            
        Returns:
            List of relevant documents
        """
        results = await self.vector_store.search(
            query=query,
            top_k=top_k,
            file_filter=file_filter,
            threshold=min_score
        )
        
        return results
    
    async def retrieve_with_context(
        self,
        query: str,
        top_k: int = 5,
        context_window: int = 1
    ) -> str:
        """
        Retrieve and format as context for LLM
        
        Args:
            query: Search query
            top_k: Number of results
            context_window: Additional context chunks
            
        Returns:
            Formatted context string
        """
        results = await self.retrieve(query, top_k)
        
        if not results:
            return "No relevant documents found."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result["source"]
            page = result.get("page", "N/A")
            content = result["content"]
            score = result["score"]
            
            context_parts.append(
                f"[Source {i}: {source} (Page {page}, Relevance: {score:.2f})]\n{content}"
            )
        
        return "\n\n---\n\n".join(context_parts)
    
    async def get_sources_summary(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get summary of sources for citations
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of source summaries
        """
        results = await self.retrieve(query, top_k)
        
        sources = []
        for result in results:
            sources.append({
                "type": "document",
                "name": result["source"],
                "page": result.get("page"),
                "relevance": result["score"],
                "snippet": result["content"][:200] + "..."
            })
        
        return sources


# Global retriever instance
_retriever: Optional[Retriever] = None


def get_retriever() -> Retriever:
    """Get global retriever instance"""
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever

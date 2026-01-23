"""
========================================
Embeddings
========================================
Text embedding generation using Gemini
"""

from typing import List
import asyncio
import google.generativeai as genai

from app.config import settings


# Configure API
genai.configure(api_key=settings.GEMINI_API_KEY)


async def get_embedding(text: str) -> List[float]:
    """
    Get embedding vector for a single text
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector (768 dimensions)
    """
    try:
        result = await asyncio.to_thread(
            genai.embed_content,
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Embedding error: {e}")
        # Return zero vector as fallback
        return [0.0] * 768


async def get_embeddings(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """
    Get embeddings for multiple texts
    
    Args:
        texts: List of texts to embed
        batch_size: Batch size for processing
        
    Returns:
        List of embedding vectors
    """
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        # Process batch (could be parallelized further)
        for text in batch:
            embedding = await get_embedding(text)
            embeddings.append(embedding)
    
    return embeddings


async def get_query_embedding(query: str) -> List[float]:
    """
    Get embedding for a search query
    Uses retrieval_query task type for better search
    
    Args:
        query: Search query
        
    Returns:
        Query embedding vector
    """
    try:
        result = await asyncio.to_thread(
            genai.embed_content,
            model="models/embedding-001",
            content=query,
            task_type="retrieval_query"
        )
        return result['embedding']
    except Exception as e:
        print(f"Query embedding error: {e}")
        return [0.0] * 768


def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings
    
    Args:
        embedding1: First embedding
        embedding2: Second embedding
        
    Returns:
        Similarity score (0 to 1)
    """
    import numpy as np
    
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # Normalize
    vec1 = vec1 / np.linalg.norm(vec1)
    vec2 = vec2 / np.linalg.norm(vec2)
    
    # Dot product = cosine similarity for normalized vectors
    return float(np.dot(vec1, vec2))

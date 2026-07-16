# Embeddings
# Text embedding generation using Gemini (LangChain version)

from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings

# Initialize LangChain Google GenAI embeddings client
_embeddings_client = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=settings.GEMINI_API_KEY
)

async def get_embedding(text: str) -> List[float]:
    # Get embedding vector for a single text using LangChain
    return await _embeddings_client.aembed_query(text)

async def get_embeddings(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    # Get embeddings for multiple texts using LangChain
    # LangChain aembed_documents handles batching/rate-limiting under the hood
    return await _embeddings_client.aembed_documents(texts)

async def get_query_embedding(query: str) -> List[float]:
    # Get embedding for a search query using LangChain
    return await _embeddings_client.aembed_query(query)

def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    # Calculate cosine similarity between two embeddings
    import numpy as np
    
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # Normalize
    vec1 = vec1 / np.linalg.norm(vec1)
    vec2 = vec2 / np.linalg.norm(vec2)
    
    # Dot product = cosine similarity for normalized vectors
    return float(np.dot(vec1, vec2))

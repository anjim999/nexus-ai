"""
========================================
Dependency Injection Container
========================================
Centralized dependencies for FastAPI
"""

from typing import Generator, Optional
from functools import lru_cache

from app.config import settings
from app.database.connection import get_db_session
from app.llm.gemini import GeminiClient
from app.rag.vectorstore import VectorStore
from app.agents.orchestrator import AgentOrchestrator


# ========================================
# Database Dependency
# ========================================
async def get_db():
    """Get database session"""
    async with get_db_session() as session:
        yield session


# ========================================
# LLM Client Dependency
# ========================================
@lru_cache()
def get_llm_client() -> GeminiClient:
    """Get cached LLM client instance"""
    return GeminiClient(api_key=settings.GEMINI_API_KEY)


# ========================================
# Vector Store Dependency
# ========================================
_vector_store: Optional[VectorStore] = None

def get_vector_store() -> VectorStore:
    """Get vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(path=settings.VECTOR_STORE_PATH)
    return _vector_store


# ========================================
# Agent Orchestrator Dependency
# ========================================
_orchestrator: Optional[AgentOrchestrator] = None

def get_orchestrator() -> AgentOrchestrator:
    """Get agent orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator(
            llm_client=get_llm_client(),
            vector_store=get_vector_store()
        )
    return _orchestrator


# ========================================
# Common Dependencies Bundle
# ========================================
class ServiceContainer:
    """Container for all services"""
    
    def __init__(self):
        self.llm = get_llm_client()
        self.vector_store = get_vector_store()
        self.orchestrator = get_orchestrator()


def get_services() -> ServiceContainer:
    """Get all services container"""
    return ServiceContainer()

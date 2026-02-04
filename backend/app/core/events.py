"""
========================================
Application Lifecycle Events
========================================
Startup and shutdown handlers
"""

import logging
from app.config import settings, validate_settings, ensure_directories
from app.database.connection import init_database
from app.rag.vectorstore import init_vector_store
from app.database.seed import seed_database_if_empty

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def startup_handler():
    """
    Execute on application startup
    """
    logger.info("🚀 Starting AI Ops Engineer...")
    
    # 1. Validate settings
    try:
        validate_settings()
        logger.info("✅ Configuration validated")
    except ValueError as e:
        logger.warning(f"⚠️ Configuration warning: {e}")
    
    # 2. Create necessary directories
    ensure_directories()
    logger.info("✅ Directories created")
    
    # 3. Initialize database
    await init_database()
    logger.info("✅ Database initialized")
    
    # 4. Auto-seed if empty
    await seed_database_if_empty()
    
    # 5. Initialize vector store
    await init_vector_store()
    logger.info("✅ Vector store initialized")
    
    logger.info("🧠 AI Ops Engineer is ready!")
    logger.info(f"📍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"📖 API Docs: http://localhost:8000/docs")


async def shutdown_handler():
    """
    Execute on application shutdown
    """
    logger.info("🛑 Shutting down AI Ops Engineer...")
    
    # Cleanup resources
    # Close database connections, save state, etc.
    
    logger.info("👋 AI Ops Engineer stopped")

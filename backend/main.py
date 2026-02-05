# AI Ops Engineer - Main Application Entry
# FastAPI application with multi-agent AI system

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config import settings
from app.core.events import startup_handler, shutdown_handler
from app.api.v1.router import api_router


# Application Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Handle startup and shutdown events
    # Startup
    await startup_handler()
    yield
    # Shutdown
    await shutdown_handler()


# Create App
app = FastAPI(
    title="AI Ops Engineer",
    description="""
    🧠 **Autonomous Business Intelligence Agent**
    
    A multi-agent AI system that analyzes business data, 
    generates insights, and automates actions.
    
    ## Features
    - 🤖 Multi-Agent System (Research, Analyst, Reasoning, Action)
    - 📄 RAG with Document Upload
    - 💬 Natural Language Queries
    - 📊 Auto-generated Visualizations
    - 🎤 Voice Input/Output
    - 📑 PDF Report Generation
    
    ## Agents
    | Agent | Role |
    |-------|------|
    | Research | Searches documents, finds context |
    | Analyst | Queries databases, runs calculations |
    | Reasoning | Synthesizes info, draws conclusions |
    | Action | Executes tasks, generates outputs |
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Routes
app.include_router(api_router, prefix="/api/v1")


# Health Check
@app.get("/health", tags=["Health"])
async def health_check():
    # Check if the API is running
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "AI Ops Engineer"
    }


@app.get("/", tags=["Root"])
async def root():
    # Root endpoint with API information
    return {
        "message": "🧠 AI Ops Engineer API",
        "description": "Autonomous Business Intelligence Agent",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    # Handle all unhandled exceptions
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
            "type": type(exc).__name__
        }
    )


# Run App
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

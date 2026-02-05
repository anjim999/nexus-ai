"""
API V1 Main Router
Combines all versioned API endpoints into a single router
"""

from fastapi import APIRouter

from app.api.v1.endpoints import chat, documents, insights, agents, reports

api_router = APIRouter()

# Include Routers

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["💬 Chat"]
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["📄 Documents"]
)

api_router.include_router(
    insights.router,
    prefix="/insights",
    tags=["📊 Insights"]
)

api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["🤖 Agents"]
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["📑 Reports"]
)

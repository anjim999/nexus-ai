"""
========================================
Chat Endpoints
========================================
Natural language chat with AI agents
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import asyncio

from app.dependencies import get_orchestrator
from app.agents.orchestrator import AgentOrchestrator

router = APIRouter()


# ========================================
# Request/Response Schemas
# ========================================
class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    sources: Optional[List[str]] = Field(default=None, description="Source citations")
    confidence: Optional[float] = Field(default=None, description="Confidence score 0-1")


class ChatRequest(BaseModel):
    """Chat request from user"""
    message: str = Field(..., min_length=1, max_length=2000, description="User's question")
    conversation_id: Optional[str] = Field(default=None, description="For conversation context")
    include_sources: bool = Field(default=True, description="Include source citations")
    stream: bool = Field(default=False, description="Stream response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Why did revenue drop last week?",
                "include_sources": True,
                "stream": False
            }
        }


class AgentStep(BaseModel):
    """Single agent execution step"""
    agent: str = Field(..., description="Agent name")
    status: str = Field(..., description="'thinking', 'done', 'error'")
    action: Optional[str] = Field(default=None, description="What agent is doing")
    result: Optional[str] = Field(default=None, description="Agent's output")
    duration_ms: Optional[int] = Field(default=None, description="Execution time")


class ChatResponse(BaseModel):
    """Chat response from AI"""
    message: str = Field(..., description="AI's response")
    conversation_id: str = Field(..., description="Conversation ID for context")
    sources: Optional[List[dict]] = Field(default=None, description="Source citations")
    confidence: float = Field(..., description="Confidence score 0-1")
    agent_steps: List[AgentStep] = Field(default=[], description="Agent execution trace")
    charts: Optional[List[dict]] = Field(default=None, description="Generated visualizations")
    actions_taken: Optional[List[str]] = Field(default=None, description="Actions executed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Based on my analysis, revenue dropped 18% last week due to...",
                "conversation_id": "conv_abc123",
                "sources": [
                    {"type": "document", "name": "sales_report.pdf", "page": 3},
                    {"type": "database", "query": "SELECT revenue FROM sales..."}
                ],
                "confidence": 0.87,
                "agent_steps": [
                    {"agent": "Research", "status": "done", "action": "Searched 3 documents"},
                    {"agent": "Analyst", "status": "done", "action": "Queried sales database"}
                ]
            }
        }


class ConversationHistory(BaseModel):
    """Full conversation history"""
    conversation_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime


# ========================================
# Endpoints
# ========================================
@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Send a message to the AI and get a response.
    
    The AI will:
    1. Analyze your question
    2. Search relevant documents (RAG)
    3. Query databases if needed
    4. Reason through the information
    5. Return an answer with sources
    """
    result = await orchestrator.process_query(
        query=request.message,
        conversation_id=request.conversation_id,
        include_sources=request.include_sources
    )
    
    return ChatResponse(
        message=result["response"],
        conversation_id=result["conversation_id"],
        sources=result.get("sources"),
        confidence=result.get("confidence", 0.8),
        agent_steps=result.get("agent_steps", []),
        charts=result.get("charts"),
        actions_taken=result.get("actions_taken")
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    Stream chat response for real-time display.
    Returns Server-Sent Events (SSE).
    """
    async def generate():
        async for chunk in orchestrator.process_query_stream(
            query=request.message,
            conversation_id=request.conversation_id
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.get("/history/{conversation_id}", response_model=ConversationHistory)
async def get_conversation_history(conversation_id: str):
    """
    Get full conversation history for a conversation ID.
    """
    # TODO: Implement conversation storage
    return ConversationHistory(
        conversation_id=conversation_id,
        messages=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@router.delete("/history/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation and its history.
    """
    # TODO: Implement deletion
    return {"status": "deleted", "conversation_id": conversation_id}


@router.get("/suggestions")
async def get_suggestions():
    """
    Get suggested questions based on available data.
    """
    return {
        "suggestions": [
            "Why did revenue change last week?",
            "Summarize the latest performance report",
            "Which customers are at risk of churning?",
            "What should we focus on this week?",
            "Show me the sales trend for this month",
            "Are there any anomalies in recent data?"
        ]
    }


# ========================================
# WebSocket for Real-time Updates
# ========================================
class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: str,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    """
    WebSocket endpoint for real-time chat and agent updates.
    """
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            # Send agent status updates
            await websocket.send_json({
                "type": "agent_status",
                "agent": "Research",
                "status": "thinking"
            })
            
            # Process query
            result = await orchestrator.process_query(
                query=message,
                conversation_id=conversation_id
            )
            
            # Send response
            await websocket.send_json({
                "type": "response",
                "data": result
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

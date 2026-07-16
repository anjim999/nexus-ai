"""
Agents Endpoints
Monitor and control AI agents
"""

from fastapi import APIRouter, Depends, WebSocket
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db

router = APIRouter()


# Enums
class AgentStatus(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    DONE = "done"
    ERROR = "error"


class AgentType(str, Enum):
    RESEARCH = "research"
    ANALYST = "analyst"
    REASONING = "reasoning"
    ACTION = "action"
    SCHEDULER = "scheduler"


# Schemas
class AgentInfo(BaseModel):
    """Information about an agent"""
    id: str
    name: str
    type: AgentType
    description: str
    status: AgentStatus = AgentStatus.IDLE
    capabilities: List[str]
    last_active: Optional[datetime] = None
    tasks_completed: int = 0


class AgentThought(BaseModel):
    """Single thought/step from an agent"""
    timestamp: datetime
    agent: str
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    confidence: Optional[float] = None


class AgentExecutionLog(BaseModel):
    """Full execution log for a query"""
    query_id: str
    query: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    agents_involved: List[str]
    thoughts: List[AgentThought]
    final_answer: Optional[str] = None
    total_duration_ms: Optional[int] = None


class AgentTaskRequest(BaseModel):
    """Request to run a specific agent task"""
    agent_type: AgentType
    task: str
    parameters: Optional[dict] = None


# Endpoints
@router.get("/", response_model=List[AgentInfo])
async def list_agents():
    """
    List all available AI agents and their status.
    """
    return [
        AgentInfo(
            id="research_agent",
            name="Research Agent",
            type=AgentType.RESEARCH,
            description="Searches documents and retrieves relevant information using RAG",
            status=AgentStatus.IDLE,
            capabilities=[
                "Document search",
                "Semantic similarity",
                "Context extraction",
                "Source citation"
            ],
            tasks_completed=127
        ),
        AgentInfo(
            id="analyst_agent",
            name="Analyst Agent",
            type=AgentType.ANALYST,
            description="Queries databases, performs calculations, and analyzes data",
            status=AgentStatus.IDLE,
            capabilities=[
                "SQL query generation",
                "Data aggregation",
                "Trend analysis",
                "Anomaly detection"
            ],
            tasks_completed=89
        ),
        AgentInfo(
            id="reasoning_agent",
            name="Reasoning Agent",
            type=AgentType.REASONING,
            description="Synthesizes information from other agents and draws conclusions",
            status=AgentStatus.IDLE,
            capabilities=[
                "Information synthesis",
                "Logical reasoning",
                "Confidence scoring",
                "Insight generation"
            ],
            tasks_completed=156
        ),
        AgentInfo(
            id="action_agent",
            name="Action Agent",
            type=AgentType.ACTION,
            description="Executes actions like sending emails, generating reports",
            status=AgentStatus.IDLE,
            capabilities=[
                "Email sending",
                "Report generation",
                "Notification dispatch",
                "API calls"
            ],
            tasks_completed=45
        ),
        AgentInfo(
            id="scheduler_agent",
            name="Scheduler Agent",
            type=AgentType.SCHEDULER,
            description="Manages scheduled tasks and automated workflows",
            status=AgentStatus.IDLE,
            capabilities=[
                "Task scheduling",
                "Recurring reports",
                "Automated monitoring",
                "Triggered actions"
            ],
            tasks_completed=234
        )
    ]


@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str):
    """
    Get details about a specific agent.
    """
    agents = await list_agents()
    for agent in agents:
        if agent.id == agent_id:
            return agent
    
    return {"error": "Agent not found"}


@router.get("/{agent_id}/logs", response_model=List[AgentExecutionLog])
async def get_agent_logs(
    agent_id: str,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent execution logs for an agent.
    """
    from sqlalchemy import text
    
    agent_name_mapping = {
        "research_agent": "Research Agent",
        "analyst_agent": "Analyst Agent",
        "reasoning_agent": "Reasoning Agent",
        "action_agent": "Action Agent",
        "scheduler_agent": "Scheduler Agent"
    }
    
    mapped_name = agent_name_mapping.get(agent_id, agent_id)
    
    # Get recent logs for this agent
    query = text("SELECT query_id, agent_name, thought, action, observation, confidence, duration_ms, created_at FROM agent_logs WHERE agent_name = :agent_name ORDER BY created_at DESC LIMIT :limit")
    result = await db.execute(query, {"agent_name": mapped_name, "limit": limit})
    logs = result.all()
    
    # Group by query_id (conversation_id)
    execution_logs = []
    seen_queries = set()
    
    for log in logs:
        if log.query_id in seen_queries:
            continue
        seen_queries.add(log.query_id)
        
        # Fetch all logs for this query to get full picture
        full_query = text("SELECT id, query_id, agent_name, thought, action, observation, confidence, duration_ms, created_at FROM agent_logs WHERE query_id = :query_id ORDER BY created_at")
        full_result = await db.execute(full_query, {"query_id": log.query_id})
        all_logs = full_result.all()
        
        thoughts = []
        agents_involved = set()
        total_duration = 0
        
        for l in all_logs:
            agents_involved.add(l.agent_name)
            if l.duration_ms:
                total_duration += l.duration_ms
            thoughts.append(
                AgentThought(
                    timestamp=l.created_at,
                    agent=l.agent_name,
                    thought=l.thought or "",
                    action=l.action,
                    observation=l.observation,
                    confidence=l.confidence
                )
            )
            
        # Get query and final answer from Message
        msg_query = text("SELECT role, content, created_at FROM messages WHERE conversation_id = :conversation_id ORDER BY created_at")
        msg_result = await db.execute(msg_query, {"conversation_id": log.query_id})
        messages = msg_result.all()
        
        user_query = "Unknown Query"
        final_answer = None
        started_at = log.created_at
        
        for m in messages:
            if str(m.role) == "user" and user_query == "Unknown Query":
                user_query = m.content
                started_at = m.created_at
            elif str(m.role) == "assistant":
                final_answer = m.content[:200] + "..." if len(m.content) > 200 else m.content
                
        execution_logs.append(
            AgentExecutionLog(
                query_id=log.query_id,
                query=user_query,
                started_at=started_at,
                completed_at=all_logs[-1].created_at if all_logs else None,
                status="completed",
                agents_involved=list(agents_involved),
                thoughts=thoughts,
                final_answer=final_answer,
                total_duration_ms=total_duration
            )
        )
        
    return execution_logs[:limit]


@router.post("/run", response_model=AgentExecutionLog)
async def run_agent_task(request: AgentTaskRequest):
    """
    Manually trigger a specific agent to run a task.
    """
    return AgentExecutionLog(
        query_id="manual_task_1",
        query=request.task,
        started_at=datetime.now(),
        status="running",
        agents_involved=[request.agent_type.value],
        thoughts=[]
    )


@router.get("/status/live")
async def get_live_status():
    """
    Get real-time status of all agents.
    """
    return {
        "agents": {
            "research": {"status": "idle", "current_task": None},
            "analyst": {"status": "idle", "current_task": None},
            "reasoning": {"status": "idle", "current_task": None},
            "action": {"status": "idle", "current_task": None},
            "scheduler": {"status": "idle", "current_task": None}
        },
        "active_queries": 0,
        "queue_length": 0,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/thoughts/{query_id}", response_model=List[AgentThought])
async def get_agent_thoughts(
    query_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the chain of thoughts for a specific query.
    Shows how agents reasoned through the problem.
    """
    from sqlalchemy import text
    
    query = text("SELECT created_at, agent_name, thought, action, observation, confidence FROM agent_logs WHERE query_id = :query_id ORDER BY created_at")
    result = await db.execute(query, {"query_id": query_id})
    logs = result.all()
    
    return [
        AgentThought(
            timestamp=log.created_at,
            agent=log.agent_name,
            thought=log.thought or "",
            action=log.action,
            observation=log.observation,
            confidence=log.confidence
        )
        for log in logs
    ]


@router.post("/{agent_id}/restart")
async def restart_agent(agent_id: str):
    """
    Restart a specific agent if it's stuck.
    """
    return {
        "agent_id": agent_id,
        "status": "restarted",
        "message": f"Agent {agent_id} has been restarted"
    }

"""
========================================
Agents Endpoints
========================================
Monitor and control AI agents
"""

from fastapi import APIRouter, Depends, WebSocket
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

router = APIRouter()


# ========================================
# Enums
# ========================================
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


# ========================================
# Schemas
# ========================================
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


# ========================================
# Endpoints
# ========================================
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
    limit: int = 10
):
    """
    Get recent execution logs for an agent.
    """
    return [
        AgentExecutionLog(
            query_id="query_123",
            query="Why did sales drop last week?",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="completed",
            agents_involved=["research", "analyst", "reasoning"],
            thoughts=[
                AgentThought(
                    timestamp=datetime.now(),
                    agent="research",
                    thought="I need to find documents related to sales",
                    action="search_documents",
                    observation="Found 3 relevant documents"
                ),
                AgentThought(
                    timestamp=datetime.now(),
                    agent="analyst",
                    thought="I should query the sales database",
                    action="sql_query",
                    observation="Retrieved 7 days of sales data"
                )
            ],
            final_answer="Sales dropped due to...",
            total_duration_ms=2340
        )
    ]


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
async def get_agent_thoughts(query_id: str):
    """
    Get the chain of thoughts for a specific query.
    Shows how agents reasoned through the problem.
    """
    return [
        AgentThought(
            timestamp=datetime.now(),
            agent="Research Agent",
            thought="The user wants to know about sales performance. Let me search relevant documents.",
            action="search_documents('sales performance')",
            observation="Found 3 documents: sales_report.pdf, quarterly_review.docx, metrics.csv",
            confidence=0.92
        ),
        AgentThought(
            timestamp=datetime.now(),
            agent="Analyst Agent",
            thought="I have context from documents. Now I should query the actual sales data.",
            action="sql_query('SELECT SUM(amount), date FROM sales GROUP BY date')",
            observation="Retrieved 30 days of sales data showing 15% decline in week 3",
            confidence=0.88
        ),
        AgentThought(
            timestamp=datetime.now(),
            agent="Reasoning Agent",
            thought="Combining document insights with data analysis. The decline correlates with...",
            action="synthesize_insights()",
            observation="Identified 3 contributing factors with high confidence",
            confidence=0.85
        )
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

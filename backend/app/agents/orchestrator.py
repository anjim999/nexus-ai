"""
========================================
Agent Orchestrator
========================================
Coordinates multiple AI agents using LangGraph
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import uuid
import asyncio
from dataclasses import dataclass, field
from enum import Enum

from app.llm.gemini import GeminiClient
from app.rag.vectorstore import VectorStore
from app.rag.retriever import get_retriever
from app.llm.prompts import (
    BASE_SYSTEM_PROMPT,
    QUERY_UNDERSTANDING_PROMPT,
    CHAT_SYSTEM_PROMPT
)


class AgentState(str, Enum):
    """Agent execution state"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    DONE = "done"
    ERROR = "error"


@dataclass
class AgentStep:
    """Single step in agent execution"""
    agent: str
    status: AgentState
    thought: Optional[str] = None
    action: Optional[str] = None
    observation: Optional[str] = None
    duration_ms: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OrchestratorState:
    """State passed between agents"""
    query: str
    conversation_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    documents: List[Dict] = field(default_factory=list)
    data_results: List[Dict] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    agent_steps: List[AgentStep] = field(default_factory=list)
    final_response: Optional[str] = None
    sources: List[Dict] = field(default_factory=list)
    confidence: float = 0.0
    charts: List[Dict] = field(default_factory=list)
    actions_taken: List[str] = field(default_factory=list)


class AgentOrchestrator:
    """
    Multi-Agent Orchestrator
    
    Coordinates the execution of multiple specialized agents:
    1. Research Agent - Document search and retrieval
    2. Analyst Agent - Data analysis and SQL queries
    3. Reasoning Agent - Synthesis and conclusions
    4. Action Agent - Execute actions and generate outputs
    
    Uses a state machine pattern for agent coordination.
    """
    
    def __init__(
        self,
        llm_client: GeminiClient = None,
        vector_store: VectorStore = None
    ):
        from app.dependencies import get_llm_client, get_vector_store
        
        self.llm = llm_client or get_llm_client()
        self.vector_store = vector_store or get_vector_store()
        self.retriever = get_retriever()
        
        # Import agents
        from app.agents.specialized.research_agent import ResearchAgent
        from app.agents.specialized.analyst_agent import AnalystAgent
        from app.agents.specialized.reasoning_agent import ReasoningAgent
        from app.agents.specialized.action_agent import ActionAgent
        
        # Initialize agents
        self.research_agent = ResearchAgent(self.llm, self.retriever)
        self.analyst_agent = AnalystAgent(self.llm)
        self.reasoning_agent = ReasoningAgent(self.llm)
        self.action_agent = ActionAgent(self.llm)
        
        # Conversation memory
        self.conversations: Dict[str, List[Dict]] = {}
    
    async def process_query(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user query through the agent pipeline
        
        Args:
            query: User's question or request
            conversation_id: Optional conversation context
            include_sources: Whether to include source citations
            
        Returns:
            Complete response with sources and agent steps
        """
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Initialize state
        state = OrchestratorState(
            query=query,
            conversation_id=conversation_id
        )
        
        try:
            # Step 1: Understand the query
            query_analysis = await self._analyze_query(query)
            state.context["query_analysis"] = query_analysis
            
            # Step 2: Research Agent - Find relevant documents
            research_step = await self._run_research_agent(state)
            state.agent_steps.append(research_step)
            
            # Step 3: Analyst Agent - Query data if needed
            if self._needs_data_analysis(query_analysis):
                analyst_step = await self._run_analyst_agent(state)
                state.agent_steps.append(analyst_step)
            
            # Step 4: Reasoning Agent - Synthesize and conclude
            reasoning_step = await self._run_reasoning_agent(state)
            state.agent_steps.append(reasoning_step)
            
            # Step 5: Action Agent - Check if actions needed
            if self._needs_action(query_analysis):
                action_step = await self._run_action_agent(state)
                state.agent_steps.append(action_step)
            
            # Store in conversation memory
            self._save_to_memory(conversation_id, query, state.final_response)
            
            # Build response
            return {
                "response": state.final_response,
                "conversation_id": conversation_id,
                "sources": state.sources if include_sources else None,
                "confidence": state.confidence,
                "agent_steps": [
                    {
                        "agent": step.agent,
                        "status": step.status.value,
                        "action": step.action,
                        "duration_ms": step.duration_ms
                    }
                    for step in state.agent_steps
                ],
                "charts": state.charts if state.charts else None,
                "actions_taken": state.actions_taken if state.actions_taken else None
            }
            
        except Exception as e:
            return {
                "response": f"I encountered an error while processing your request: {str(e)}",
                "conversation_id": conversation_id,
                "sources": None,
                "confidence": 0.0,
                "agent_steps": [
                    {
                        "agent": "orchestrator",
                        "status": "error",
                        "action": str(e)
                    }
                ],
                "charts": None,
                "actions_taken": None
            }
    
    async def process_query_stream(
        self,
        query: str,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process query with streaming updates
        
        Yields status updates as agents work
        """
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        state = OrchestratorState(
            query=query,
            conversation_id=conversation_id
        )
        
        # Yield initial status
        yield {"type": "status", "message": "Understanding your question..."}
        
        # Analyze query
        query_analysis = await self._analyze_query(query)
        state.context["query_analysis"] = query_analysis
        
        # Research
        yield {"type": "agent_start", "agent": "research", "status": "thinking"}
        research_step = await self._run_research_agent(state)
        state.agent_steps.append(research_step)
        yield {
            "type": "agent_done",
            "agent": "research",
            "result": f"Found {len(state.documents)} relevant documents"
        }
        
        # Analyst (if needed)
        if self._needs_data_analysis(query_analysis):
            yield {"type": "agent_start", "agent": "analyst", "status": "thinking"}
            analyst_step = await self._run_analyst_agent(state)
            state.agent_steps.append(analyst_step)
            yield {
                "type": "agent_done",
                "agent": "analyst",
                "result": "Data analysis complete"
            }
        
        # Reasoning
        yield {"type": "agent_start", "agent": "reasoning", "status": "thinking"}
        reasoning_step = await self._run_reasoning_agent(state)
        state.agent_steps.append(reasoning_step)
        yield {
            "type": "agent_done",
            "agent": "reasoning",
            "result": "Synthesis complete"
        }
        
        # Stream final response
        yield {"type": "response_start"}
        yield {"type": "response_chunk", "content": state.final_response}
        yield {"type": "response_end", "sources": state.sources}
    
    # ========================================
    # Agent Runners
    # ========================================
    async def _run_research_agent(self, state: OrchestratorState) -> AgentStep:
        """Run the research agent"""
        import time
        start = time.time()
        
        step = AgentStep(
            agent="Research Agent",
            status=AgentState.THINKING
        )
        
        try:
            # Search for relevant documents
            results = await self.research_agent.search(state.query)
            
            state.documents = results.get("documents", [])
            state.sources.extend(results.get("sources", []))
            
            step.status = AgentState.DONE
            step.action = f"Searched documents, found {len(state.documents)} relevant chunks"
            step.observation = results.get("summary", "")
            
        except Exception as e:
            step.status = AgentState.ERROR
            step.observation = str(e)
        
        step.duration_ms = int((time.time() - start) * 1000)
        return step
    
    async def _run_analyst_agent(self, state: OrchestratorState) -> AgentStep:
        """Run the analyst agent"""
        import time
        start = time.time()
        
        step = AgentStep(
            agent="Analyst Agent",
            status=AgentState.THINKING
        )
        
        try:
            # Analyze data
            results = await self.analyst_agent.analyze(
                query=state.query,
                context=state.documents
            )
            
            state.data_results = results.get("data", [])
            if results.get("chart"):
                state.charts.append(results["chart"])
            
            step.status = AgentState.DONE
            step.action = results.get("action", "Analyzed data")
            step.observation = results.get("summary", "")
            
        except Exception as e:
            step.status = AgentState.ERROR
            step.observation = str(e)
        
        step.duration_ms = int((time.time() - start) * 1000)
        return step
    
    async def _run_reasoning_agent(self, state: OrchestratorState) -> AgentStep:
        """Run the reasoning agent"""
        import time
        start = time.time()
        
        step = AgentStep(
            agent="Reasoning Agent",
            status=AgentState.THINKING
        )
        
        try:
            # Synthesize all information
            results = await self.reasoning_agent.reason(
                query=state.query,
                documents=state.documents,
                data=state.data_results,
                context=state.context
            )
            
            state.final_response = results.get("response", "")
            state.confidence = results.get("confidence", 0.8)
            state.insights = results.get("insights", [])
            
            step.status = AgentState.DONE
            step.thought = results.get("reasoning", "")
            step.action = "Synthesized information"
            
        except Exception as e:
            step.status = AgentState.ERROR
            step.observation = str(e)
            state.final_response = "I was unable to process your request."
        
        step.duration_ms = int((time.time() - start) * 1000)
        return step
    
    async def _run_action_agent(self, state: OrchestratorState) -> AgentStep:
        """Run the action agent"""
        import time
        start = time.time()
        
        step = AgentStep(
            agent="Action Agent",
            status=AgentState.THINKING
        )
        
        try:
            # Determine and execute actions
            results = await self.action_agent.execute(
                query=state.query,
                response=state.final_response,
                context=state.context
            )
            
            state.actions_taken = results.get("actions", [])
            
            step.status = AgentState.DONE
            step.action = f"Executed {len(state.actions_taken)} actions"
            step.observation = ", ".join(state.actions_taken)
            
        except Exception as e:
            step.status = AgentState.ERROR
            step.observation = str(e)
        
        step.duration_ms = int((time.time() - start) * 1000)
        return step
    
    # ========================================
    # Helper Methods
    # ========================================
    async def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query to determine processing path"""
        prompt = QUERY_UNDERSTANDING_PROMPT.format(query=query)
        
        try:
            result = await self.llm.generate_json(
                prompt=prompt,
                schema={
                    "intent": "string",
                    "entities": ["list of strings"],
                    "time_range": "string or null",
                    "data_sources": ["list of strings"],
                    "output_type": "string"
                }
            )
            return result
        except Exception:
            return {
                "intent": "question",
                "entities": [],
                "time_range": None,
                "data_sources": ["documents"],
                "output_type": "text"
            }
    
    def _needs_data_analysis(self, analysis: Dict) -> bool:
        """Check if query needs data analysis"""
        keywords = ["how much", "how many", "trend", "compare", "total", "average"]
        query_lower = analysis.get("intent", "").lower()
        
        for keyword in keywords:
            if keyword in query_lower:
                return True
        
        if "database" in analysis.get("data_sources", []):
            return True
        
        return False
    
    def _needs_action(self, analysis: Dict) -> bool:
        """Check if query needs action execution"""
        action_keywords = ["send", "create", "generate", "email", "report", "schedule"]
        intent = analysis.get("intent", "").lower()
        
        for keyword in action_keywords:
            if keyword in intent:
                return True
        
        return analysis.get("output_type") in ["report", "action"]
    
    def _save_to_memory(self, conversation_id: str, query: str, response: str):
        """Save exchange to conversation memory"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        self.conversations[conversation_id].append({
            "role": "user",
            "content": query,
            "timestamp": datetime.now().isoformat()
        })
        self.conversations[conversation_id].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        return self.conversations.get(conversation_id, [])
    
    def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

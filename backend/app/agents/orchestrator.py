# Agent Orchestrator
# Coordinates multiple AI agents using LangGraph

from typing import Dict, Any, List, Optional, AsyncGenerator, TypedDict
from datetime import datetime
import uuid
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from langgraph.graph import StateGraph, END

from app.llm.gemini import GeminiClient
from app.rag.vectorstore import VectorStore
from app.rag.retriever import get_retriever
from app.llm.prompts import (
    BASE_SYSTEM_PROMPT,
    QUERY_UNDERSTANDING_PROMPT,
    CHAT_SYSTEM_PROMPT
)


class AgentState(str, Enum):
    # Agent execution state
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    DONE = "done"
    ERROR = "error"


@dataclass
class AgentStep:
    # Single step in agent execution (retained for backward compatibility if needed)
    agent: str
    status: AgentState
    thought: Optional[str] = None
    action: Optional[str] = None
    observation: Optional[str] = None
    duration_ms: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)


# State schema for LangGraph
class GraphState(TypedDict):
    query: str
    conversation_id: str
    context: Dict[str, Any]
    documents: List[Dict[str, Any]]
    data_results: List[Dict[str, Any]]
    insights: List[str]
    agent_steps: List[Dict[str, Any]]
    final_response: Optional[str]
    sources: List[Dict[str, Any]]
    confidence: float
    charts: List[Dict[str, Any]]
    actions_taken: List[str]


class AgentOrchestrator:
    # Multi-Agent Orchestrator using LangGraph
    # Coordinates the execution of multiple specialized agents: Research, Analyst, Reasoning, Action, Scheduler
    
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
        from app.agents.specialized.scheduler_agent import SchedulerAgent
        
        # Initialize agents
        self.research_agent = ResearchAgent(self.llm, self.retriever)
        self.analyst_agent = AnalystAgent(self.llm)
        self.reasoning_agent = ReasoningAgent(self.llm)
        self.action_agent = ActionAgent(self.llm)
        self.scheduler_agent = SchedulerAgent(self.llm)
        
        # Database repository
        from app.database.repositories.chat import chat_repo
        self.chat_repo = chat_repo
        
        # Build LangGraph workflow
        workflow = StateGraph(GraphState)
        
        # Add Nodes
        workflow.add_node("analyze_query", self._node_analyze_query)
        workflow.add_node("research", self._node_research_agent)
        workflow.add_node("analyst", self._node_analyst_agent)
        workflow.add_node("reasoning", self._node_reasoning_agent)
        workflow.add_node("action", self._node_action_agent)
        workflow.add_node("scheduler", self._node_scheduler_agent)
        
        # Define Entry Point
        workflow.set_entry_point("analyze_query")
        
        # Define Edges
        workflow.add_edge("analyze_query", "research")
        
        # Routing after Research
        def route_after_research(state: GraphState) -> str:
            query_analysis = state.get("context", {}).get("query_analysis", {})
            if self._needs_data_analysis(query_analysis, state.get("query", "")):
                return "analyst"
            return "reasoning"
            
        workflow.add_conditional_edges(
            "research",
            route_after_research,
            {
                "analyst": "analyst",
                "reasoning": "reasoning"
            }
        )
        
        workflow.add_edge("analyst", "reasoning")
        
        # Routing after Reasoning
        def route_after_reasoning(state: GraphState) -> str:
            query_analysis = state.get("context", {}).get("query_analysis", {})
            if self._needs_action(query_analysis):
                return "action"
            if self._needs_scheduling(query_analysis):
                return "scheduler"
            return END
            
        workflow.add_conditional_edges(
            "reasoning",
            route_after_reasoning,
            {
                "action": "action",
                "scheduler": "scheduler",
                END: END
            }
        )
        
        # Routing after Action
        def route_after_action(state: GraphState) -> str:
            query_analysis = state.get("context", {}).get("query_analysis", {})
            if self._needs_scheduling(query_analysis):
                return "scheduler"
            return END
            
        workflow.add_conditional_edges(
            "action",
            route_after_action,
            {
                "scheduler": "scheduler",
                END: END
            }
        )
        
        workflow.add_edge("scheduler", END)
        
        # Compile the graph
        self.app = workflow.compile()
    
    # LangGraph Nodes
    async def _node_analyze_query(self, state: GraphState) -> Dict[str, Any]:
        query_analysis = await self._analyze_query(state["query"])
        return {
            "context": {**state.get("context", {}), "query_analysis": query_analysis}
        }
        
    async def _node_research_agent(self, state: GraphState) -> Dict[str, Any]:
        import time
        start = time.time()
        
        step = {
            "agent": "Research Agent",
            "status": "thinking",
            "action": "Searching documents"
        }
        
        try:
            results = await self.research_agent.search(state["query"])
            
            new_documents = list(state.get("documents", [])) + results.get("documents", [])
            new_sources = list(state.get("sources", [])) + results.get("sources", [])
            
            step["status"] = "done"
            step["action"] = f"Searched documents, found {len(results.get('documents', []))} relevant chunks"
            step["duration_ms"] = int((time.time() - start) * 1000)
            
            return {
                "documents": new_documents,
                "sources": new_sources,
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }
        except Exception as e:
            step["status"] = "error"
            step["action"] = str(e)
            step["duration_ms"] = int((time.time() - start) * 1000)
            return {
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }

    async def _node_analyst_agent(self, state: GraphState) -> Dict[str, Any]:
        import time
        start = time.time()
        
        step = {
            "agent": "Analyst Agent",
            "status": "thinking",
            "action": "Analyzing data"
        }
        
        try:
            results = await self.analyst_agent.analyze(
                query=state["query"],
                context=state["documents"]
            )
            
            new_data = list(state.get("data_results", [])) + results.get("data", [])
            new_charts = list(state.get("charts", []))
            if results.get("chart"):
                new_charts.append(results["chart"])
                
            step["status"] = "done"
            step["action"] = results.get("action", "Analyzed data")
            step["duration_ms"] = int((time.time() - start) * 1000)
            
            return {
                "data_results": new_data,
                "charts": new_charts,
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }
        except Exception as e:
            step["status"] = "error"
            step["action"] = str(e)
            step["duration_ms"] = int((time.time() - start) * 1000)
            return {
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }

    async def _node_reasoning_agent(self, state: GraphState) -> Dict[str, Any]:
        import time
        start = time.time()
        
        step = {
            "agent": "Reasoning Agent",
            "status": "thinking",
            "action": "Synthesizing information"
        }
        
        try:
            results = await self.reasoning_agent.reason(
                query=state["query"],
                documents=state["documents"],
                data=state["data_results"],
                context=state["context"]
            )
            
            step["status"] = "done"
            step["action"] = "Synthesized information"
            step["duration_ms"] = int((time.time() - start) * 1000)
            
            return {
                "final_response": results.get("response", ""),
                "confidence": results.get("confidence", 0.8),
                "insights": results.get("insights", []),
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }
        except Exception as e:
            step["status"] = "error"
            step["action"] = f"Error: {str(e)}"
            step["duration_ms"] = int((time.time() - start) * 1000)
            return {
                "final_response": "I was unable to process your request.",
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }

    async def _node_action_agent(self, state: GraphState) -> Dict[str, Any]:
        import time
        start = time.time()
        
        step = {
            "agent": "Action Agent",
            "status": "thinking",
            "action": "Executing actions"
        }
        
        try:
            results = await self.action_agent.execute(
                query=state["query"],
                response=state["final_response"],
                context=state["context"]
            )
            
            new_actions = list(state.get("actions_taken", [])) + results.get("actions", [])
            
            step["status"] = "done"
            step["action"] = f"Executed {len(results.get('actions', []))} actions"
            step["duration_ms"] = int((time.time() - start) * 1000)
            
            return {
                "actions_taken": new_actions,
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }
        except Exception as e:
            step["status"] = "error"
            step["action"] = str(e)
            step["duration_ms"] = int((time.time() - start) * 1000)
            return {
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }

    async def _node_scheduler_agent(self, state: GraphState) -> Dict[str, Any]:
        import time
        start = time.time()
        
        step = {
            "agent": "Scheduler Agent",
            "status": "thinking",
            "action": "Scheduling task"
        }
        
        try:
            results = await self.scheduler_agent.schedule(
                query=state["query"],
                context=state["context"]
            )
            
            step["status"] = "done"
            step["action"] = f"Scheduled task: {results.get('job_details', {}).get('task_name', 'Unknown')}"
            step["duration_ms"] = int((time.time() - start) * 1000)
            
            resp = state.get("final_response", "") or ""
            if resp:
                resp += f"\n\n[Scheduler]: {results.get('message')}"
            else:
                resp = f"[Scheduler]: {results.get('message')}"
                
            return {
                "final_response": resp,
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }
        except Exception as e:
            step["status"] = "error"
            step["action"] = str(e)
            step["duration_ms"] = int((time.time() - start) * 1000)
            return {
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }
            
    # API Entry Points
    async def process_query(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        # Process a user query through the compiled LangGraph pipeline
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        initial_state: GraphState = {
            "query": query,
            "conversation_id": conversation_id,
            "context": {},
            "documents": [],
            "data_results": [],
            "insights": [],
            "agent_steps": [],
            "final_response": None,
            "sources": [],
            "confidence": 0.0,
            "charts": [],
            "actions_taken": []
        }
        
        try:
            # Invoke compiled StateGraph
            final_state = await self.app.ainvoke(initial_state)
            
            # Store in database
            await self._save_to_memory(
                conversation_id, 
                query, 
                final_state.get("final_response", "") or "",
                final_state
            )
            
            # Build response
            return {
                "response": final_state.get("final_response", ""),
                "conversation_id": conversation_id,
                "sources": final_state.get("sources") if include_sources else None,
                "confidence": final_state.get("confidence", 0.0),
                "agent_steps": final_state.get("agent_steps", []),
                "charts": final_state.get("charts") if final_state.get("charts") else None,
                "actions_taken": final_state.get("actions_taken") if final_state.get("actions_taken") else None
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
        # Process query with streaming updates using LangGraph astream
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        initial_state: GraphState = {
            "query": query,
            "conversation_id": conversation_id,
            "context": {},
            "documents": [],
            "data_results": [],
            "insights": [],
            "agent_steps": [],
            "final_response": None,
            "sources": [],
            "confidence": 0.0,
            "charts": [],
            "actions_taken": []
        }
        
        # Yield initial status
        yield {"type": "status", "message": "Understanding your question..."}
        
        # Pre-yield the start of the first active step (research)
        yield {"type": "agent_start", "agent": "research", "status": "thinking"}
        
        final_state = dict(initial_state)
        
        try:
            # Consume the stream of graph state updates
            async for event in self.app.astream(initial_state):
                for node_name, node_output in event.items():
                    # Merge outputs into final_state
                    for key, val in node_output.items():
                        final_state[key] = val
                    
                    # Yield completed status and schedule start status for next node
                    if node_name == "analyze_query":
                        pass
                    elif node_name == "research":
                        yield {
                            "type": "agent_done",
                            "agent": "research",
                            "result": f"Found {len(node_output.get('documents', []))} relevant documents"
                        }
                        query_analysis = final_state.get("context", {}).get("query_analysis", {})
                        if self._needs_data_analysis(query_analysis, query):
                            yield {"type": "agent_start", "agent": "analyst", "status": "thinking"}
                        else:
                            yield {"type": "agent_start", "agent": "reasoning", "status": "thinking"}
                            
                    elif node_name == "analyst":
                        yield {
                            "type": "agent_done",
                            "agent": "analyst",
                            "result": "Data analysis complete"
                        }
                        yield {"type": "agent_start", "agent": "reasoning", "status": "thinking"}
                        
                    elif node_name == "reasoning":
                        yield {
                            "type": "agent_done",
                            "agent": "reasoning",
                            "result": "Synthesis complete"
                        }
                        query_analysis = final_state.get("context", {}).get("query_analysis", {})
                        if self._needs_action(query_analysis):
                            yield {"type": "agent_start", "agent": "action", "status": "executing"}
                        elif self._needs_scheduling(query_analysis):
                            yield {"type": "agent_start", "agent": "scheduler", "status": "planning"}
                            
                    elif node_name == "action":
                        yield {
                            "type": "agent_done",
                            "agent": "action",
                            "result": f"Executed {len(node_output.get('actions_taken', []))} actions"
                        }
                        query_analysis = final_state.get("context", {}).get("query_analysis", {})
                        if self._needs_scheduling(query_analysis):
                            yield {"type": "agent_start", "agent": "scheduler", "status": "planning"}
                            
                    elif node_name == "scheduler":
                        yield {
                            "type": "agent_done",
                            "agent": "scheduler",
                            "result": "Task scheduled"
                        }
            
            # Save to database memory
            await self._save_to_memory(
                conversation_id, 
                query, 
                final_state.get("final_response", "") or "",
                final_state
            )
            
            # Stream final response
            yield {"type": "response_start"}
            yield {"type": "response_chunk", "content": final_state.get("final_response", "") or ""}
            yield {
                "type": "response_end", 
                "data": {
                    "conversation_id": conversation_id,
                    "sources": final_state.get("sources"),
                    "confidence": final_state.get("confidence", 0.0),
                    "agent_steps": final_state.get("agent_steps"),
                    "charts": final_state.get("charts"),
                    "actions_taken": final_state.get("actions_taken")
                }
            }
            
        except Exception as e:
            yield {
                "type": "status",
                "message": f"Error occurred: {str(e)}"
            }
            
    # Helper Methods
    async def _analyze_query(self, query: str) -> Dict[str, Any]:
        # Analyze query to determine processing path
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
    
    def _needs_data_analysis(self, analysis: Dict, query: str = "") -> bool:
        # Check if query needs data analysis
        keywords = ["how much", "how many", "trend", "compare", "total", "average", "calculate", "sum", "count"]
        
        # Check intent
        intent = analysis.get("intent", "").lower()
        for keyword in keywords:
            if keyword in intent:
                return True
                
        # Check original query
        query_lower = query.lower()
        for keyword in keywords:
            if keyword in query_lower:
                return True
        
        if "database" in analysis.get("data_sources", []):
            return True
        
        return False
    
    def _needs_action(self, analysis: Dict) -> bool:
        # Check if query needs action execution
        action_keywords = ["send", "create", "generate", "email", "report", "schedule"]
        intent = analysis.get("intent", "").lower()
        
        for keyword in action_keywords:
            if keyword in intent:
                return True
        
        return analysis.get("output_type") in ["report", "action"]

    def _needs_scheduling(self, analysis: Dict) -> bool:
        # Check if query needs scheduling
        keywords = ["schedule", "remind", "daily", "weekly", "monthly", "every", "tomorrow", "recurring", "automate"]
        intent = analysis.get("intent", "").lower()
        
        for keyword in keywords:
            if keyword in intent:
                return True
        
        return False
    
    async def _save_to_memory(
        self, 
        conversation_id: str, 
        query: str, 
        response: str,
        state: Dict[str, Any]
    ):
        # Save exchange to database
        # Save User Message
        await self.chat_repo.add_message(
            conversation_id=conversation_id,
            role="user",
            content=query
        )
        
        # Format agent steps for storage
        steps_data = []
        for step in state.get("agent_steps", []):
            steps_data.append({
                "agent": step.get("agent"),
                "status": step.get("status"),
                "action": step.get("action"),
                "duration_ms": step.get("duration_ms")
            })
        
        # Save Assistant Message with metadata
        await self.chat_repo.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response,
            sources=state.get("sources"),
            confidence=state.get("confidence", 0.8),
            agent_steps=steps_data
        )
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        # Get conversation history from database
        return await self.chat_repo.get_history(conversation_id)
    
    async def clear_conversation(self, conversation_id: str):
        # Clear conversation history (Not implemented for DB yet to preserve data)
        pass

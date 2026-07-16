# Agent Orchestrator
# Coordinates multiple AI agents using LangGraph

from typing import Dict, Any, List, Optional, AsyncGenerator, TypedDict
from datetime import datetime
import uuid
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from langgraph.graph import StateGraph, END, START

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
        workflow.add_edge(START, "analyze_query")
        
        # Routing after Query Analysis
        def route_after_analysis(state: GraphState) -> str:
            query_analysis = state.get("context", {}).get("query_analysis", {})
            sources = query_analysis.get("data_sources", [])
            # If database is targeted and documents is NOT targeted, go straight to analyst
            if "database" in sources and "documents" not in sources:
                return "analyst"
            return "research"
            
        workflow.add_conditional_edges(
            "analyze_query",
            route_after_analysis,
            {
                "research": "research",
                "analyst": "analyst"
            }
        )
        
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
            if self._needs_action(query_analysis, state.get("query", "")):
                return "action"
            if self._needs_scheduling(query_analysis, state.get("query", "")):
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
            if self._needs_scheduling(query_analysis, state.get("query", "")):
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
        
    async def _log_agent_step(self, query_id: str, step: Dict[str, Any]):
        from app.database.connection import AsyncSessionLocal
        from sqlalchemy import text
        from datetime import datetime
        async with AsyncSessionLocal() as session:
            stmt = text("""
                INSERT INTO agent_logs (query_id, agent_name, thought, action, observation, confidence, duration_ms, created_at)
                VALUES (:query_id, :agent_name, :thought, :action, :observation, :confidence, :duration_ms, :created_at)
            """)
            await session.execute(stmt, {
                "query_id": query_id,
                "agent_name": step.get("agent", "Unknown"),
                "thought": step.get("thought", ""),
                "action": step.get("action", ""),
                "observation": step.get("observation", ""),
                "confidence": step.get("confidence"),
                "duration_ms": step.get("duration_ms"),
                "created_at": datetime.utcnow()
            })
            await session.commit()
    
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
            
            await self._log_agent_step(state["conversation_id"], step)
            
            return {
                "documents": new_documents,
                "sources": new_sources,
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }
        except Exception as e:
            step["status"] = "error"
            step["action"] = str(e)
            step["duration_ms"] = int((time.time() - start) * 1000)
            await self._log_agent_step(state["conversation_id"], step)
            raise

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
            
            await self._log_agent_step(state["conversation_id"], step)
            
            return {
                "data_results": new_data,
                "charts": new_charts,
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }
        except Exception as e:
            step["status"] = "error"
            step["action"] = str(e)
            step["duration_ms"] = int((time.time() - start) * 1000)
            await self._log_agent_step(state["conversation_id"], step)
            raise

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
            
            await self._log_agent_step(state["conversation_id"], step)
            
            return {
                "insights": results.get("insights", []),
                "final_response": results.get("response"),
                "confidence": results.get("confidence", 0.8),
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }
        except Exception as e:
            step["status"] = "error"
            step["action"] = f"Error: {str(e)}"
            step["duration_ms"] = int((time.time() - start) * 1000)
            await self._log_agent_step(state["conversation_id"], step)
            raise

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
            
            await self._log_agent_step(state["conversation_id"], step)
            
            # Build action details summary to append to response
            action_details = []
            for r in results.get("results", []):
                if r.get("status") == "success":
                    result_info = r.get("result", {})
                    if r["action"] == "send_email":
                        recipients = result_info.get("recipients", [])
                        subject = result_info.get("subject", "N/A")
                        action_details.append(f"📧 Email sent to: {', '.join(recipients) if recipients else 'N/A'} | Subject: {subject} | Status: {result_info.get('status', 'sent')}")
                    elif r["action"] == "schedule_task":
                        action_details.append(f"⏰ Scheduled: {result_info.get('name', 'N/A')} | Frequency: {result_info.get('frequency', 'N/A')}")
                    elif r["action"] == "generate_report":
                        action_details.append(f"📄 Report generated: {result_info.get('title', 'N/A')} | Type: {result_info.get('type', 'N/A')}")
                    else:
                        action_details.append(f"✅ {r['action']}: success")
            
            resp = state.get("final_response", "") or ""
            if action_details:
                details_text = "\n".join(action_details)
                if resp:
                    resp += f"\n\n**Actions Executed:**\n{details_text}"
                else:
                    resp = f"**Actions Executed:**\n{details_text}"
            
            return {
                "final_response": resp,
                "actions_taken": new_actions,
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }
        except Exception as e:
            step["status"] = "error"
            step["action"] = str(e)
            step["duration_ms"] = int((time.time() - start) * 1000)
            await self._log_agent_step(state["conversation_id"], step)
            raise

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
            job = results.get('job_details', {})
            task_name = job.get('task_name', 'Unknown')
            step["action"] = f"Scheduled task: {task_name}"
            step["duration_ms"] = int((time.time() - start) * 1000)
            
            await self._log_agent_step(state["conversation_id"], step)
            
            # Build detailed scheduler message
            cron_expr = job.get('cron_expression', 'N/A')
            priority = job.get('priority', 'N/A')
            schedule_type = job.get('schedule_type', 'N/A')
            scheduler_msg = f"\n\n**[Scheduler]:** ✅ Scheduled task '{task_name}' successfully.\n- Schedule Type: {schedule_type}\n- Cron Expression: `{cron_expr}`\n- Priority: {priority}"
            
            resp = state.get("final_response", "") or ""
            if resp:
                resp += scheduler_msg
            else:
                resp = scheduler_msg
                
            return {
                "final_response": resp,
                "agent_steps": list(state.get("agent_steps", [])) + [step]
            }
        except Exception as e:
            step["status"] = "error"
            step["action"] = str(e)
            step["duration_ms"] = int((time.time() - start) * 1000)
            await self._log_agent_step(state["conversation_id"], step)
            raise
            
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
        
        # Fast local greeting/FAQ bypass check
        conversational_response = self._check_conversational_query(query)
        if conversational_response:
            await self._save_to_memory(
                conversation_id,
                query,
                conversational_response,
                {"sources": [], "confidence": 1.0, "agent_steps": []}
            )
            return {
                "response": conversational_response,
                "conversation_id": conversation_id,
                "sources": None,
                "confidence": 1.0,
                "agent_steps": [
                    {
                        "agent": "orchestrator",
                        "status": "done",
                        "action": "Bypassed LLM pipeline for greeting/FAQ query (saved API quota)"
                    }
                ],
                "charts": None,
                "actions_taken": None
            }
            
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
        
        # Fast local greeting/FAQ bypass check
        conversational_response = self._check_conversational_query(query)
        if conversational_response:
            # Yield initial status
            yield {"type": "status", "message": "Analyzing greeting..."}
            await asyncio.sleep(0.1)
            
            # Save message exchange to memory
            await self._save_to_memory(
                conversation_id,
                query,
                conversational_response,
                {"sources": [], "confidence": 1.0, "agent_steps": []}
            )
            
            # Yield websocket events with typewriter effect
            yield {"type": "response_start"}
            words = conversational_response.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield {"type": "response_chunk", "content": chunk}
                await asyncio.sleep(0.015)  # Fast typing animation
                
            yield {
                "type": "response_end",
                "data": {
                    "conversation_id": conversation_id,
                    "sources": None,
                    "confidence": 1.0,
                    "agent_steps": [
                        {
                            "agent": "orchestrator",
                            "status": "done",
                            "action": "Bypassed LLM pipeline for greeting/FAQ query (saved API quota)"
                        }
                    ],
                    "charts": None,
                    "actions_taken": None
                }
            }
            return
            
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
                        if self._needs_action(query_analysis, query):
                            yield {"type": "agent_start", "agent": "action", "status": "executing"}
                        elif self._needs_scheduling(query_analysis, query):
                            yield {"type": "agent_start", "agent": "scheduler", "status": "planning"}
                            
                    elif node_name == "action":
                        yield {
                            "type": "agent_done",
                            "agent": "action",
                            "result": f"Executed {len(node_output.get('actions_taken', []))} actions"
                        }
                        query_analysis = final_state.get("context", {}).get("query_analysis", {})
                        if self._needs_scheduling(query_analysis, query):
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
            error_msg = f"Error occurred: {str(e)}"
            friendly_msg = "I encountered an error while processing your request, likely due to AI rate limits. Please wait a moment and try again."
            if "RetryError" in error_msg or "429" in error_msg:
                error_msg = "Google Gemini Rate Limit Exceeded (429 Too Many Requests)."
            
            yield {
                "type": "status",
                "message": error_msg
            }
            yield {
                "type": "response_chunk",
                "content": friendly_msg
            }
            yield {
                "type": "response_end",
                "data": {
                    "conversation_id": conversation_id,
                    "final_response": friendly_msg,
                    "confidence": 0.0,
                    "agent_steps": final_state.get("agent_steps", []) + [
                        {
                            "agent": "orchestrator",
                            "status": "error",
                            "action": error_msg
                        }
                    ]
                }
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
    
    def _needs_action(self, analysis: Dict, query: str = "") -> bool:
        # Check if query needs action execution
        action_keywords = ["send", "create", "generate", "email", "report", "schedule", "mail"]
        intent = analysis.get("intent", "").lower()
        
        for keyword in action_keywords:
            if keyword in intent:
                return True
                
        # Check original query
        query_lower = query.lower()
        for keyword in action_keywords:
            if keyword in query_lower:
                return True
        
        return analysis.get("output_type") in ["report", "action"]

    def _needs_scheduling(self, analysis: Dict, query: str = "") -> bool:
        # Check if query needs scheduling
        keywords = ["schedule", "remind", "daily", "weekly", "monthly", "every", "tomorrow", "recurring", "automate"]
        intent = analysis.get("intent", "").lower()
        
        for keyword in keywords:
            if keyword in intent:
                return True
                
        # Check original query
        query_lower = query.lower()
        for keyword in keywords:
            if keyword in query_lower:
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
        
        # Check if conversation needs an AI-generated title
        try:
            from app.database.connection import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as session:
                stmt = text("SELECT title FROM conversations WHERE id = :id")
                res = await session.execute(stmt, {"id": conversation_id})
                title = res.scalar()
                
                title_clean = title.strip().lower() if title else ""
                query_clean = query.strip().lower()
                
                # If title is default, empty, or is just a direct slice of the query, we generate a clean one
                is_default = title_clean in ("", "new conversation", "new chat", "none")
                is_query_slice = (title_clean == query_clean) or (query_clean.startswith(title_clean) and len(title_clean) <= 50)
                
                if is_default or is_query_slice:
                    await self._generate_and_save_title(conversation_id, query)
        except Exception as e:
            print(f"Error checking conversation for title generation: {e}")

    async def _generate_and_save_title(self, conversation_id: str, query: str):
        # Generate a punchy 3-5 word title using Gemini based on first query
        try:
            title_prompt = (
                "Generate a short, punchy 3-to-5 word title representing the following user request. "
                "Respond with ONLY the title text itself, without any quotes, brackets, markdown, or surrounding explanation. "
                "Keep it brief and professional.\n\n"
                f"User Request: {query}"
            )
            ai_title = await self.llm.generate(title_prompt)
            
            # Clean wrapping quotes, spaces, and trailing punctuation
            ai_title = ai_title.strip()
            while ai_title and ai_title[0] in ('"', "'", "`", "*", "[", "("):
                ai_title = ai_title[1:]
            while ai_title and ai_title[-1] in ('"', "'", "`", "*", "]", ")", ".", "!", "?"):
                ai_title = ai_title[:-1]
            ai_title = ai_title.strip()
            
            if ai_title and len(ai_title) < 100:
                from app.database.connection import AsyncSessionLocal
                from sqlalchemy import text
                from datetime import datetime
                
                async with AsyncSessionLocal() as session:
                    stmt = text("UPDATE conversations SET title = :title, updated_at = :updated_at WHERE id = :id")
                    await session.execute(stmt, {
                        "title": ai_title,
                        "updated_at": datetime.utcnow(),
                        "id": conversation_id
                    })
                    await session.commit()
                    print(f"--- AI generated title for {conversation_id}: '{ai_title}' ---")
        except Exception as e:
            print(f"Failed to generate AI title: {e}")
            
    def _check_conversational_query(self, query: str) -> Optional[str]:
        # Fast local check for common greetings and small talk to save API costs
        clean_query = query.strip().lower().rstrip("?!.")
        
        greetings = {
            "hi", "hello", "hey", "hola", "greetings", "yo", "sup", "hi there", "hello there",
            "good morning", "good afternoon", "good evening"
        }
        
        if clean_query in greetings:
            import random
            greetings_responses = [
                "Hello! I'm Nexus AI, your autonomous operational intelligence agent. How can I help you analyze your business data today? "
                "You can ask me to search customer feedback documents, query product sales trends, or schedule automated tasks.",
                
                "Hi there! Welcome to Nexus AI. I'm ready to help you retrieve insights and run calculations. "
                "What business metrics or documents are we looking into today?",
                
                "Greetings! I'm here to assist with your data operations. Feel free to ask me questions about your uploaded documents, "
                "sales tables, or ask me to schedule recurring alerts."
            ]
            return random.choice(greetings_responses)
            
        if "how are you" in clean_query or "how's it going" in clean_query or "how is it going" in clean_query:
            return (
                "I'm running at peak efficiency, thank you for asking! I am ready to help you analyze sales trends, "
                "extract insights from documents, or automate your operational tasks. What can I do for you today?"
            )
            
        intro_queries = {
            "who are you", "what are you", "what is your name", "tell me about yourself",
            "what can you do", "what is this", "how can you help me", "help"
        }
        if clean_query in intro_queries or any(x in clean_query for x in ["what can you do", "how can you help", "who are you"]):
            return (
                "I am **Nexus AI**, an Autonomous Business Intelligence Agent built to streamline your data operations. "
                "Here is what I can do for you:\n\n"
                "*   **📄 Document Intelligence**: Retrieve facts and summarize information across your uploaded knowledge bases (PDFs, CSVs, TXT, JSON).\n"
                "*   **📊 Database Analysis**: Write and run SQL queries to calculate business metrics (like sales, average costs, churn risks).\n"
                "*   **📑 Operational Reporting**: Generate visual trends and reports from your calculations.\n"
                "*   **⚙️ Automation & Scheduling**: Set up automated schedules for recurring tasks (e.g., daily database backups, weekly email reports).\n\n"
                "What would you like to explore first?"
            )
            
        return None
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        # Get conversation history from database
        return await self.chat_repo.get_history(conversation_id)
    
    async def clear_conversation(self, conversation_id: str):
        # Clear conversation history (Not implemented for DB yet to preserve data)
        pass

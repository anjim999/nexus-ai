"""
========================================
Scheduler Agent
========================================
Manages scheduled tasks and automated workflows
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid

from app.llm.gemini import GeminiClient

class SchedulerAgent:
    """
    Scheduler Agent
    
    Responsibilities:
    - Schedule recurring tasks
    - Manage automated workflows
    - specific cron-like job definitions
    - Check conflicts
    """
    
    def __init__(self, llm: GeminiClient):
        self.llm = llm
        # Simulated job store
        self.jobs = {} # In memory store for demo
        
        self.system_prompt = """
You are the Scheduler Agent.
Your role is to parse natural language requests into structured scheduling configurations.

Output JSON only:
{
    "task_name": "string",
    "schedule_type": "one_time" | "recurring",
    "cron_expression": "string (standard cron format)",
    "priority": "high" | "medium" | "low",
    "description": "string"
}
"""

    async def schedule(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Parse request and schedule a task
        """
        print(f"⏰ Scheduler parsing: {query}")
        
        prompt = f"""
Parse the following scheduling request into a configuration:
Request: {query}

Current Date: {datetime.now().isoformat()}

Return the JSON configuration.
"""
        try:
            config = await self.llm.generate_json(
                prompt=prompt,
                schema={
                    "task_name": "string",
                    "schedule_type": "string",
                    "cron_expression": "string",
                    "priority": "string",
                    "description": "string"
                },
                system_prompt=self.system_prompt
            )
            
            # Simulate saving to a job queue
            job_id = str(uuid.uuid4())
            job_record = {
                "id": job_id,
                "created_at": datetime.now().isoformat(),
                "status": "scheduled",
                **config
            }
            self.jobs[job_id] = job_record
            
            return {
                "status": "success",
                "message": f"Scheduled task '{config['task_name']}' successfully.",
                "job_details": job_record
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to schedule task: {str(e)}"
            }

    async def list_jobs(self) -> List[Dict]:
        """List all active jobs"""
        return list(self.jobs.values())

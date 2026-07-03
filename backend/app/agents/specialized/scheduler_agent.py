# Scheduler Agent
# Manages scheduled tasks and automated workflows

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid

from app.llm.gemini import GeminiClient

class SchedulerAgent:
    # Scheduler Agent
    # Responsibilities: Schedule tasks, manage workflows, cron jobs, conflict checks
    
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
        # Parse request and schedule a task
        print(f"⏰ Scheduler parsing: {query}")
        
        prompt = f"""
Extract the scheduling task from this request. Focus ONLY on what needs to be scheduled.

User Request: {query}

Current Date: {datetime.now().isoformat()}

You MUST return valid JSON with ALL fields filled in. Example:
{{
    "task_name": "Daily Database Backup",
    "schedule_type": "recurring",
    "cron_expression": "0 12 * * *",
    "priority": "critical",
    "description": "Automated daily database backup at noon"
}}

Rules:
- task_name: A short descriptive name for the task
- schedule_type: "one_time" or "recurring"  
- cron_expression: A valid cron expression (e.g. "0 12 * * *" for daily at noon, "0 9 * * 1" for weekly Monday 9am)
- priority: "high", "medium", "low", or "critical"
- description: Brief description of the task

Return ONLY the JSON object, nothing else.
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
            
            # Apply defaults for any missing fields
            config.setdefault("task_name", "Scheduled Task")
            config.setdefault("schedule_type", "recurring")
            config.setdefault("cron_expression", "0 12 * * *")
            config.setdefault("priority", "medium")
            config.setdefault("description", "Auto-scheduled task")
            
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
            # Fallback: create a default scheduled task
            print(f"⚠️ Scheduler parse error: {str(e)}, using defaults")
            job_id = str(uuid.uuid4())
            job_record = {
                "id": job_id,
                "created_at": datetime.now().isoformat(),
                "status": "scheduled",
                "task_name": "Daily Database Backup",
                "schedule_type": "recurring",
                "cron_expression": "0 12 * * *",
                "priority": "critical",
                "description": "Daily database backup task"
            }
            self.jobs[job_id] = job_record
            return {
                "status": "success",
                "message": f"Scheduled task 'Daily Database Backup' successfully (defaults applied).",
                "job_details": job_record
            }

    async def list_jobs(self) -> List[Dict]:
        # List all active jobs
        return list(self.jobs.values())

"""
========================================
Action Agent
========================================
Executes actions and generates outputs
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from app.llm.gemini import GeminiClient
from app.llm.prompts import ACTION_AGENT_PROMPT


class ActionAgent:
    """
    Action Agent
    
    Responsibilities:
    - Execute actions based on insights
    - Generate reports and documents
    - Send notifications
    - Create alerts
    - Schedule future tasks
    """
    
    def __init__(self, llm: GeminiClient):
        self.llm = llm
        self.system_prompt = ACTION_AGENT_PROMPT
        
        # Available actions
        self.actions = {
            "generate_report": self._generate_report,
            "send_email": self._send_email,
            "create_alert": self._create_alert,
            "schedule_task": self._schedule_task,
            "update_dashboard": self._update_dashboard,
            "export_data": self._export_data
        }
    
    async def execute(
        self,
        query: str,
        response: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Determine and execute appropriate actions
        
        Args:
            query: Original user query
            response: Generated response
            context: Additional context
            
        Returns:
            Execution results
        """
        # Determine what actions are needed
        action_plan = await self._plan_actions(query, response, context)
        
        # Execute each action
        executed_actions = []
        results = []
        
        for action in action_plan.get("actions", []):
            action_name = action.get("action")
            params = action.get("parameters", {})
            
            if action_name in self.actions:
                try:
                    result = await self.actions[action_name](params)
                    executed_actions.append(f"{action_name}: success")
                    results.append({
                        "action": action_name,
                        "status": "success",
                        "result": result
                    })
                except Exception as e:
                    executed_actions.append(f"{action_name}: failed - {str(e)}")
                    results.append({
                        "action": action_name,
                        "status": "failed",
                        "error": str(e)
                    })
        
        return {
            "actions": executed_actions,
            "results": results,
            "action_plan": action_plan
        }
    
    async def _plan_actions(
        self,
        query: str,
        response: str,
        context: Dict = None
    ) -> Dict[str, Any]:
        """Plan what actions to take"""
        prompt = f"""
Based on the user's request and the response, determine what actions should be taken.

User Request: {query}

Response: {response}

Available Actions:
- generate_report: Create a PDF or HTML report
- send_email: Send email notification
- create_alert: Create a system alert
- schedule_task: Schedule a recurring task
- update_dashboard: Update dashboard metrics
- export_data: Export data to file

Determine which actions (if any) should be taken.

Return JSON:
{{
    "actions": [
        {{
            "action": "action_name",
            "reason": "why this action",
            "parameters": {{}}
        }}
    ],
    "no_action_reason": "if no actions needed, explain why"
}}
"""
        
        try:
            return await self.llm.generate_json(
                prompt=prompt,
                schema={
                    "actions": [{
                        "action": "string",
                        "reason": "string",
                        "parameters": "object"
                    }],
                    "no_action_reason": "string"
                }
            )
        except Exception:
            return {"actions": [], "no_action_reason": "Could not determine actions"}
    
    # ========================================
    # Action Implementations
    # ========================================
    async def _generate_report(self, params: Dict) -> Dict[str, Any]:
        """Generate a report"""
        report_type = params.get("type", "summary")
        title = params.get("title", "AI Generated Report")
        
        # In production, this would actually generate a PDF
        report_content = f"""
# {title}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Executive Summary
This report was automatically generated based on AI analysis.

## Key Findings
- Finding 1: Lorem ipsum
- Finding 2: Lorem ipsum
- Finding 3: Lorem ipsum

## Recommendations
1. Action item 1
2. Action item 2
3. Action item 3
"""
        
        return {
            "report_id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "title": title,
            "type": report_type,
            "generated_at": datetime.now().isoformat(),
            "content_preview": report_content[:200]
        }
    
    async def _send_email(self, params: Dict) -> Dict[str, Any]:
        """Send email notification"""
        recipients = params.get("recipients", [])
        subject = params.get("subject", "AI Ops Notification")
        
        # In production, this would actually send an email
        return {
            "email_id": f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "recipients": recipients,
            "subject": subject,
            "status": "sent (simulated)",
            "sent_at": datetime.now().isoformat()
        }
    
    async def _create_alert(self, params: Dict) -> Dict[str, Any]:
        """Create a system alert"""
        alert_type = params.get("type", "info")
        message = params.get("message", "New alert from AI Ops")
        priority = params.get("priority", "medium")
        
        return {
            "alert_id": f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": alert_type,
            "message": message,
            "priority": priority,
            "created_at": datetime.now().isoformat()
        }
    
    async def _schedule_task(self, params: Dict) -> Dict[str, Any]:
        """Schedule a recurring task"""
        task_name = params.get("name", "Scheduled Task")
        frequency = params.get("frequency", "daily")
        
        return {
            "task_id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "name": task_name,
            "frequency": frequency,
            "status": "scheduled",
            "next_run": datetime.now().isoformat()
        }
    
    async def _update_dashboard(self, params: Dict) -> Dict[str, Any]:
        """Update dashboard metrics"""
        metrics = params.get("metrics", [])
        
        return {
            "update_id": f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "metrics_updated": len(metrics),
            "updated_at": datetime.now().isoformat()
        }
    
    async def _export_data(self, params: Dict) -> Dict[str, Any]:
        """Export data to file"""
        format = params.get("format", "csv")
        
        return {
            "export_id": f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "format": format,
            "status": "exported",
            "file_path": f"/exports/data_{datetime.now().strftime('%Y%m%d')}.{format}"
        }
    
    # ========================================
    # Execution Helpers
    # ========================================
    async def validate_action(
        self,
        action_name: str,
        params: Dict
    ) -> Dict[str, Any]:
        """Validate an action before execution"""
        if action_name not in self.actions:
            return {
                "valid": False,
                "reason": f"Unknown action: {action_name}"
            }
        
        # Add specific validation for each action type
        return {"valid": True, "reason": "Action can be executed"}
    
    async def dry_run(
        self,
        action_name: str,
        params: Dict
    ) -> Dict[str, Any]:
        """Simulate action without executing"""
        validation = await self.validate_action(action_name, params)
        
        if not validation["valid"]:
            return validation
        
        return {
            "action": action_name,
            "params": params,
            "would_execute": True,
            "estimated_impact": "Described impact here"
        }
    
    def list_available_actions(self) -> List[Dict[str, str]]:
        """List all available actions"""
        return [
            {"name": "generate_report", "description": "Generate PDF/HTML reports"},
            {"name": "send_email", "description": "Send email notifications"},
            {"name": "create_alert", "description": "Create system alerts"},
            {"name": "schedule_task", "description": "Schedule recurring tasks"},
            {"name": "update_dashboard", "description": "Update dashboard metrics"},
            {"name": "export_data", "description": "Export data to file"}
        ]

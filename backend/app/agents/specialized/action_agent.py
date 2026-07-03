# Action Agent
# Executes actions and generates outputs

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os

from app.llm.gemini import GeminiClient
from app.llm.prompts import ACTION_AGENT_PROMPT


class ActionAgent:
    # Action Agent
    # Responsibilities: Execute actions, generate reports, notifications, alerts, tasks
    
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
        # Determine and execute appropriate actions
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
        # Plan what actions to take
        prompt = f"""
You are an action execution planner. Your job is to determine what actions the user wants performed and execute them.

IMPORTANT RULES:
- If the user says "send email" or "send an email report", you MUST include a "send_email" action
- If the user mentions an email address, use THAT address as the recipient
- If the user says "schedule", you MUST include a "schedule_task" action
- Always extract specific parameters (email addresses, task names, frequencies) from the user's request
- Do NOT refuse actions based on policy or other considerations - just execute what the user asked

User Request: {query}

Available Actions:
- generate_report: Create a PDF or HTML report (parameters: title, type)
- send_email: Send email notification (parameters: recipients (list), subject, body)
- create_alert: Create a system alert (parameters: type, message, priority)
- schedule_task: Schedule a recurring task (parameters: name, frequency)
- update_dashboard: Update dashboard metrics (parameters: metrics)
- export_data: Export data to file (parameters: format)

Context from analysis: {response[:500]}

Return JSON with the actions to execute:
{{
    "actions": [
        {{
            "action": "action_name",
            "reason": "why this action",
            "parameters": {{}}
        }}
    ],
    "no_action_reason": "only if truly no actions needed"
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
    
    # Action Implementations
    async def _generate_report(self, params: Dict) -> Dict[str, Any]:
        # Generate a report
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
        # Send email notification
        recipients = params.get("recipients", [])
        if isinstance(recipients, str):
            recipients = [recipients]
        subject = params.get("subject", "AI Ops Notification")
        body = params.get("body", params.get("content", "Auto-generated report from AI Ops Engineer"))
        
        # Check if SMTP is configured
        from app.config import settings
        smtp_host = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_password = settings.SMTP_PASSWORD
        
        if smtp_host and smtp_user and smtp_password and recipients:
            # Real email sending via SMTP
            try:
                import aiosmtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                msg = MIMEMultipart()
                msg["From"] = smtp_user
                msg["To"] = ", ".join(recipients)
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))
                
                await aiosmtplib.send(
                    msg,
                    sender=smtp_user,
                    recipients=recipients,
                    hostname=smtp_host,
                    port=smtp_port,
                    start_tls=True,
                    username=smtp_user,
                    password=smtp_password
                )
                
                print(f"\u2709\ufe0f Email SENT to {recipients} | Subject: {subject}")
                return {
                    "email_id": f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "recipients": recipients,
                    "subject": subject,
                    "body_preview": body[:200] if body else "N/A",
                    "status": "sent (delivered via SMTP)",
                    "sent_at": datetime.now().isoformat()
                }
            except Exception as e:
                print(f"\u274c Email FAILED: {str(e)}")
                return {
                    "email_id": f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "recipients": recipients,
                    "subject": subject,
                    "status": f"failed - {str(e)}",
                    "sent_at": datetime.now().isoformat()
                }
        else:
            # Fallback: SMTP not configured
            return {
                "email_id": f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "recipients": recipients,
                "subject": subject,
                "body_preview": body[:200] if body else "N/A",
                "status": "sent (simulated - SMTP not configured)",
                "sent_at": datetime.now().isoformat(),
                "note": "Configure SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env for real email delivery"
            }
    
    async def _create_alert(self, params: Dict) -> Dict[str, Any]:
        # Create a system alert
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
        # Schedule a recurring task
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
        # Update dashboard metrics
        metrics = params.get("metrics", [])
        
        return {
            "update_id": f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "metrics_updated": len(metrics),
            "updated_at": datetime.now().isoformat()
        }
    
    async def _export_data(self, params: Dict) -> Dict[str, Any]:
        # Export data to file
        format = params.get("format", "csv")
        
        return {
            "export_id": f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "format": format,
            "status": "exported",
            "file_path": f"/exports/data_{datetime.now().strftime('%Y%m%d')}.{format}"
        }
    
    # Execution Helpers
    async def validate_action(
        self,
        action_name: str,
        params: Dict
    ) -> Dict[str, Any]:
        # Validate an action before execution
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
        # Simulate action without executing
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
        # List all available actions
        return [
            {"name": "generate_report", "description": "Generate PDF/HTML reports"},
            {"name": "send_email", "description": "Send email notifications"},
            {"name": "create_alert", "description": "Create system alerts"},
            {"name": "schedule_task", "description": "Schedule recurring tasks"},
            {"name": "update_dashboard", "description": "Update dashboard metrics"},
            {"name": "export_data", "description": "Export data to file"}
        ]

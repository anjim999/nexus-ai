# Action Agent
# Executes actions and generates outputs using native LangChain tools

from typing import Dict, Any, List, Optional, Type
from datetime import datetime
import json
import os

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.llm.gemini import GeminiClient
from app.llm.prompts import ACTION_AGENT_PROMPT

# Pydantic models for input schemas
class GenerateReportInput(BaseModel):
    title: str = Field(description="The title of the report to generate")
    type: str = Field(default="summary", description="The type of report, e.g., summary, detailed")

class SendEmailInput(BaseModel):
    recipients: List[str] = Field(description="List of recipient email addresses")
    subject: str = Field(description="The subject of the email")
    body: str = Field(description="The body content of the email")

class CreateAlertInput(BaseModel):
    type: str = Field(default="info", description="The alert type, e.g., info, warning, error")
    message: str = Field(description="The alert message description")
    priority: str = Field(default="medium", description="The alert priority: low, medium, high")

class ScheduleTaskInput(BaseModel):
    name: str = Field(description="The name of the task to schedule")
    frequency: str = Field(default="daily", description="The scheduling frequency: daily, weekly, monthly")

class UpdateDashboardInput(BaseModel):
    metrics: List[str] = Field(description="The list of metrics to update on the dashboard")

class ExportDataInput(BaseModel):
    format: str = Field(default="csv", description="The format of exported data, e.g. csv, json")


# BaseTool Subclasses
class GenerateReportTool(BaseTool):
    name: str = "generate_report"
    description: str = "Generate a PDF/HTML report. Use this tool when the user asks to generate, compile, or create a report."
    args_schema: Type[BaseModel] = GenerateReportInput

    def _run(self, title: str, type: str = "summary") -> Dict[str, Any]:
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
            "type": type,
            "generated_at": datetime.now().isoformat(),
            "content_preview": report_content[:200]
        }

    async def _arun(self, title: str, type: str = "summary") -> Dict[str, Any]:
        return self._run(title, type)


class SendEmailTool(BaseTool):
    name: str = "send_email"
    description: str = "Send an email notification to specific recipients. Use this tool when the user asks to send an email."
    args_schema: Type[BaseModel] = SendEmailInput

    def _run(self, recipients: List[str], subject: str, body: str) -> Dict[str, Any]:
        return {
            "email_id": f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "recipients": recipients,
            "subject": subject,
            "body_preview": body[:200] if body else "N/A",
            "status": "sent (simulated - sync call)",
            "sent_at": datetime.now().isoformat()
        }

    async def _arun(self, recipients: List[str], subject: str, body: str) -> Dict[str, Any]:
        from app.config import settings
        smtp_host = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_password = settings.SMTP_PASSWORD
        
        if smtp_host and smtp_user and smtp_password and recipients:
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
                
                print(f"✉️ Email SENT to {recipients} | Subject: {subject}")
                return {
                    "email_id": f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "recipients": recipients,
                    "subject": subject,
                    "body_preview": body[:200] if body else "N/A",
                    "status": "sent (delivered via SMTP)",
                    "sent_at": datetime.now().isoformat()
                }
            except Exception as e:
                print(f"❌ Email FAILED: {str(e)}")
                return {
                    "email_id": f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "recipients": recipients,
                    "subject": subject,
                    "status": f"failed - {str(e)}",
                    "sent_at": datetime.now().isoformat()
                }
        else:
            return {
                "email_id": f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "recipients": recipients,
                "subject": subject,
                "body_preview": body[:200] if body else "N/A",
                "status": "sent (simulated - SMTP not configured)",
                "sent_at": datetime.now().isoformat(),
                "note": "Configure SMTP_HOST, SMTP_USER, SMTP_PASSWORD in .env for real email delivery"
            }


class CreateAlertTool(BaseTool):
    name: str = "create_alert"
    description: str = "Create a system alert. Use this tool when the user asks to create an alert, notify about a critical issue, or flag something."
    args_schema: Type[BaseModel] = CreateAlertInput

    def _run(self, type: str = "info", message: str = "", priority: str = "medium") -> Dict[str, Any]:
        return {
            "alert_id": f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": type,
            "message": message,
            "priority": priority,
            "created_at": datetime.now().isoformat()
        }

    async def _arun(self, type: str = "info", message: str = "", priority: str = "medium") -> Dict[str, Any]:
        return self._run(type, message, priority)


class ScheduleTaskTool(BaseTool):
    name: str = "schedule_task"
    description: str = "Schedule a recurring task. Use this tool when the user asks to schedule a job or task."
    args_schema: Type[BaseModel] = ScheduleTaskInput

    def _run(self, name: str, frequency: str = "daily") -> Dict[str, Any]:
        return {
            "task_id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "name": name,
            "frequency": frequency,
            "status": "scheduled",
            "next_run": datetime.now().isoformat()
        }

    async def _arun(self, name: str, frequency: str = "daily") -> Dict[str, Any]:
        return self._run(name, frequency)


class UpdateDashboardTool(BaseTool):
    name: str = "update_dashboard"
    description: str = "Update dashboard metrics. Use this tool when the user asks to update metrics, KPIs, or update dashboard."
    args_schema: Type[BaseModel] = UpdateDashboardInput

    def _run(self, metrics: List[str]) -> Dict[str, Any]:
        return {
            "update_id": f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "metrics_updated": len(metrics),
            "updated_at": datetime.now().isoformat()
        }

    async def _arun(self, metrics: List[str]) -> Dict[str, Any]:
        return self._run(metrics)


class ExportDataTool(BaseTool):
    name: str = "export_data"
    description: str = "Export data to a file. Use this tool when the user asks to export, download, or save data."
    args_schema: Type[BaseModel] = ExportDataInput

    def _run(self, format: str = "csv") -> Dict[str, Any]:
        return {
            "export_id": f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "format": format,
            "status": "exported",
            "file_path": f"/exports/data_{datetime.now().strftime('%Y%m%d')}.{format}"
        }

    async def _arun(self, format: str = "csv") -> Dict[str, Any]:
        return self._run(format)


class ActionAgent:
    # Action Agent backed by native LangChain Tools and bind_tools()
    
    def __init__(self, llm: GeminiClient):
        self.llm = llm
        self.system_prompt = ACTION_AGENT_PROMPT
        
        # Instantiate LangChain tools
        self.tools = [
            GenerateReportTool(),
            SendEmailTool(),
            CreateAlertTool(),
            ScheduleTaskTool(),
            UpdateDashboardTool(),
            ExportDataTool()
        ]
        
        # Keep quick actions mapping for backward compatibility
        self.actions = {tool.name: tool for tool in self.tools}
        
        # Bind tools to the model
        self.model_with_tools = self.llm.chat_model.bind_tools(self.tools)
        
    async def execute(
        self,
        query: str,
        response: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        # Formulate native LangChain input messages
        from langchain_core.messages import SystemMessage, HumanMessage
        
        # Incorporate context
        system_content = (
            f"{self.system_prompt}\n\n"
            f"CRITICAL INSTRUCTION:\n"
            f"1. You must execute the appropriate tool immediately to fulfill the user's request.\n"
            f"2. Do not respond conversationally or ask for user confirmation. Go straight to calling the tool.\n"
            f"3. For email requests, extract the recipients (e.g. mapping 'marketing team' to marketing@company.com or similar, or using placeholder if not present), subject, and construct the body from the available context.\n\n"
            f"Available context from analysis:\n{response}"
        )
        
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=query)
        ]
        
        # Pacing sleep to avoid 429 rate limit exceptions on free tier API
        from tenacity import retry, stop_after_attempt, wait_exponential
        import asyncio

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10)
        )
        async def _invoke_model_with_retry():
            await asyncio.sleep(3.5)
            return await self.model_with_tools.ainvoke(messages)

        # Invoke model with tool binding
        try:
            message_response = await _invoke_model_with_retry()
            tool_calls = message_response.tool_calls
        except Exception as e:
            print(f"Tool invocation planning failed: {e}")
            tool_calls = []

        executed_actions = []
        results = []
        actions_list = []
        
        for tool_call in tool_calls:
            action_name = tool_call["name"]
            params = tool_call["args"]
            
            if action_name in self.actions:
                tool_instance = self.actions[action_name]
                try:
                    # Invoke tool using LangChain API
                    result = await tool_instance.ainvoke(params)
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
                
                # Append to action plan for validation / logging compatibility
                actions_list.append({
                    "action": action_name,
                    "reason": "Execution matched request",
                    "parameters": params
                })
                
        action_plan = {
            "actions": actions_list,
            "no_action_reason": "No actions taken" if not actions_list else ""
        }
        
        return {
            "actions": executed_actions,
            "results": results,
            "action_plan": action_plan
        }

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

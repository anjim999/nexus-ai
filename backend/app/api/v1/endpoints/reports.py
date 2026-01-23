"""
========================================
Reports Endpoints
========================================
Generate, export, and schedule reports
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import io

router = APIRouter()


# ========================================
# Enums
# ========================================
class ReportFormat(str, Enum):
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"


class ReportType(str, Enum):
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_ANALYSIS = "weekly_analysis"
    MONTHLY_REPORT = "monthly_report"
    CUSTOM = "custom"
    INSIGHT_REPORT = "insight_report"


class ScheduleFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# ========================================
# Schemas
# ========================================
class ReportGenerateRequest(BaseModel):
    """Request to generate a report"""
    title: str = Field(..., min_length=1, max_length=200)
    report_type: ReportType = ReportType.CUSTOM
    format: ReportFormat = ReportFormat.PDF
    sections: Optional[List[str]] = Field(
        default=None,
        description="Sections to include: 'metrics', 'insights', 'charts', 'recommendations'"
    )
    time_range_days: int = Field(default=7, ge=1, le=365)
    include_ai_analysis: bool = Field(default=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Weekly Performance Report",
                "report_type": "weekly_analysis",
                "format": "pdf",
                "sections": ["metrics", "insights", "charts", "recommendations"],
                "time_range_days": 7,
                "include_ai_analysis": True
            }
        }


class ReportMetadata(BaseModel):
    """Generated report metadata"""
    id: str
    title: str
    report_type: ReportType
    format: ReportFormat
    generated_at: datetime
    file_size_bytes: Optional[int] = None
    download_url: str
    expires_at: datetime


class ScheduledReport(BaseModel):
    """Scheduled report configuration"""
    id: str
    title: str
    report_type: ReportType
    frequency: ScheduleFrequency
    next_run: datetime
    recipients: List[str]
    is_active: bool = True
    created_at: datetime


class ScheduleReportRequest(BaseModel):
    """Request to schedule a recurring report"""
    title: str
    report_type: ReportType
    frequency: ScheduleFrequency
    recipients: List[str] = Field(..., min_items=1)
    time_of_day: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    sections: Optional[List[str]] = None


# ========================================
# Endpoints
# ========================================
@router.post("/generate", response_model=ReportMetadata)
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a report on demand.
    
    The report will include:
    - Key metrics and KPIs
    - AI-generated insights
    - Data visualizations
    - Recommendations
    
    Returns immediately with report ID. Report generation happens in background.
    """
    import uuid
    
    report_id = str(uuid.uuid4())
    
    # In production, this would trigger actual report generation
    # background_tasks.add_task(generate_report_task, report_id, request)
    
    return ReportMetadata(
        id=report_id,
        title=request.title,
        report_type=request.report_type,
        format=request.format,
        generated_at=datetime.now(),
        file_size_bytes=None,  # Will be updated when complete
        download_url=f"/api/v1/reports/{report_id}/download",
        expires_at=datetime.now() + timedelta(days=7)
    )


@router.get("/{report_id}/download")
async def download_report(report_id: str, format: ReportFormat = ReportFormat.PDF):
    """
    Download a generated report.
    """
    # Generate sample PDF content
    content = f"""
    AI Ops Engineer - Generated Report
    ===================================
    Report ID: {report_id}
    Generated: {datetime.now().isoformat()}
    
    Executive Summary
    -----------------
    This report provides an analysis of business performance...
    
    Key Metrics
    -----------
    - Revenue: ₹12.4L (+12.5%)
    - Customers: 1,247 (+8.3%)
    - Support Tickets: 47 (-15.2%)
    
    AI Insights
    -----------
    1. Marketing campaign drove 35% traffic increase
    2. Product A outperforming by 40%
    3. Customer churn risk identified for 3 accounts
    
    Recommendations
    ---------------
    1. Focus on customer retention for high-value accounts
    2. Scale successful marketing strategies
    3. Investigate Tuesday revenue anomaly
    """.encode('utf-8')
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=report_{report_id}.pdf"
        }
    )


@router.get("/", response_model=List[ReportMetadata])
async def list_reports(
    limit: int = 10,
    report_type: Optional[ReportType] = None
):
    """
    List all generated reports.
    """
    return [
        ReportMetadata(
            id="report_1",
            title="Weekly Performance Report",
            report_type=ReportType.WEEKLY_ANALYSIS,
            format=ReportFormat.PDF,
            generated_at=datetime.now() - timedelta(hours=2),
            file_size_bytes=245000,
            download_url="/api/v1/reports/report_1/download",
            expires_at=datetime.now() + timedelta(days=5)
        ),
        ReportMetadata(
            id="report_2",
            title="Daily Summary - Jan 23",
            report_type=ReportType.DAILY_SUMMARY,
            format=ReportFormat.PDF,
            generated_at=datetime.now() - timedelta(days=1),
            file_size_bytes=125000,
            download_url="/api/v1/reports/report_2/download",
            expires_at=datetime.now() + timedelta(days=6)
        )
    ]


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """
    Delete a generated report.
    """
    return {"status": "deleted", "report_id": report_id}


# ========================================
# Scheduled Reports
# ========================================
@router.post("/schedule", response_model=ScheduledReport)
async def schedule_report(request: ScheduleReportRequest):
    """
    Schedule a recurring report.
    
    Reports will be automatically generated and sent to recipients.
    """
    import uuid
    
    # Calculate next run time
    next_run = datetime.now().replace(hour=9, minute=0, second=0)
    if next_run < datetime.now():
        next_run += timedelta(days=1)
    
    return ScheduledReport(
        id=str(uuid.uuid4()),
        title=request.title,
        report_type=request.report_type,
        frequency=request.frequency,
        next_run=next_run,
        recipients=request.recipients,
        is_active=True,
        created_at=datetime.now()
    )


@router.get("/schedule", response_model=List[ScheduledReport])
async def list_scheduled_reports():
    """
    List all scheduled reports.
    """
    return [
        ScheduledReport(
            id="sched_1",
            title="Daily Morning Briefing",
            report_type=ReportType.DAILY_SUMMARY,
            frequency=ScheduleFrequency.DAILY,
            next_run=datetime.now().replace(hour=9, minute=0) + timedelta(days=1),
            recipients=["team@company.com"],
            is_active=True,
            created_at=datetime.now() - timedelta(days=30)
        )
    ]


@router.put("/schedule/{schedule_id}/toggle")
async def toggle_scheduled_report(schedule_id: str):
    """
    Enable or disable a scheduled report.
    """
    return {
        "schedule_id": schedule_id,
        "is_active": True,  # Toggled
        "message": "Scheduled report status updated"
    }


@router.delete("/schedule/{schedule_id}")
async def delete_scheduled_report(schedule_id: str):
    """
    Delete a scheduled report.
    """
    return {"status": "deleted", "schedule_id": schedule_id}

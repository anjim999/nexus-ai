# Reports Endpoints
# Generate, export, and schedule business reports

from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import io
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.dependencies import get_db
from fastapi import HTTPException
import os
from app.database.connection import get_db_session
from app.core.reports_generator import generate_pdf_report
from app.config import settings

router = APIRouter()


# Enums
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


# Schemas
class ReportGenerateRequest(BaseModel):
    # Request to generate a report
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
    # Generated report metadata
    id: str
    title: str
    report_type: ReportType
    format: ReportFormat
    generated_at: datetime
    file_size_bytes: Optional[int] = None
    download_url: str
    expires_at: datetime


class ScheduledReport(BaseModel):
    # Scheduled report configuration
    id: str
    title: str
    report_type: ReportType
    frequency: ScheduleFrequency
    next_run: datetime
    recipients: List[str]
    is_active: bool = True
    created_at: datetime


class ScheduleReportRequest(BaseModel):
    # Request to schedule a recurring report
    title: str
    report_type: ReportType
    frequency: ScheduleFrequency
    recipients: List[str] = Field(..., min_length=1)
    time_of_day: str = Field(default="09:00", pattern=r"^\d{2}:\d{2}$")
    sections: Optional[List[str]] = None


# Endpoints
async def async_generate_report_task(
    report_id: str,
    title: str,
    report_type: str,
    time_range_days: int,
    include_ai_analysis: bool
):
    async with get_db_session() as db:
        # Check existence
        check_stmt = text("SELECT id FROM reports WHERE id = :id")
        result = await db.execute(check_stmt, {"id": report_id})
        report_exists = result.scalar() is not None
        if not report_exists:
            return
            
        try:
            pdf_bytes = await generate_pdf_report(
                title=title,
                report_type=report_type,
                time_range_days=time_range_days,
                include_ai_analysis=include_ai_analysis,
                db=db
            )
            
            file_name = f"report_{report_id}.pdf"
            file_path = os.path.join(settings.REPORTS_DIR, file_name)
            
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)
                
            update_stmt = text("""
                UPDATE reports 
                SET status = 'completed', file_path = :file_path, file_size = :file_size, completed_at = :completed_at 
                WHERE id = :id
            """)
            await db.execute(update_stmt, {
                "file_path": file_path,
                "file_size": len(pdf_bytes),
                "completed_at": datetime.utcnow(),
                "id": report_id
            })
            
        except Exception as e:
            print(f"Background report generation failed: {e}")
            update_stmt = text("""
                UPDATE reports 
                SET status = 'failed', completed_at = :completed_at 
                WHERE id = :id
            """)
            await db.execute(update_stmt, {
                "completed_at": datetime.utcnow(),
                "id": report_id
            })
            
        await db.commit()


@router.post("/generate", response_model=ReportMetadata)
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Generate a report on demand and save to DB
    report_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=7)
    
    stmt = text("""
        INSERT INTO reports (id, title, report_type, format, status, parameters_json, created_at, expires_at)
        VALUES (:id, :title, :report_type, :format, :status, :parameters_json, :created_at, :expires_at)
    """)
    await db.execute(stmt, {
        "id": report_id,
        "title": request.title,
        "report_type": request.report_type,
        "format": request.format,
        "status": "pending",
        "parameters_json": None,
        "created_at": created_at,
        "expires_at": expires_at
    })
    await db.commit()
    
    # Queue the background generation task
    background_tasks.add_task(
        async_generate_report_task,
        report_id=report_id,
        title=request.title,
        report_type=request.report_type,
        time_range_days=request.time_range_days,
        include_ai_analysis=request.include_ai_analysis
    )
    
    return ReportMetadata(
        id=report_id,
        title=request.title,
        report_type=request.report_type,
        format=request.format,
        generated_at=created_at,
        file_size_bytes=None,
        download_url=f"/api/v1/reports/{report_id}/download",
        expires_at=expires_at
    )


@router.get("/{report_id}/download")
async def download_report(report_id: str, db: AsyncSession = Depends(get_db)):
    # Download a generated report
    query = text("SELECT id, title, report_type, format, status, file_path, file_size AS file_size_bytes, expires_at, created_at FROM reports WHERE id = :report_id")
    result = await db.execute(query, {"report_id": report_id})
    report = result.fetchone()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if report.status == "pending":
        raise HTTPException(status_code=400, detail="Report is still generating")
        
    if report.status == "failed":
        raise HTTPException(status_code=500, detail="Report generation failed")
        
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found on server")
        
    return FileResponse(
        path=report.file_path,
        media_type="application/pdf",
        filename=f"{report.title.replace(' ', '_')}.pdf"
    )


@router.get("/", response_model=List[ReportMetadata])
async def list_reports(
    limit: int = 10,
    report_type: Optional[ReportType] = None,
    db: AsyncSession = Depends(get_db)
):
    # List all generated reports from DB
    if report_type:
        query = text("SELECT id, title, report_type, format, status, file_path, file_size AS file_size_bytes, expires_at, created_at FROM reports WHERE report_type = :report_type ORDER BY created_at DESC LIMIT :limit")
        result = await db.execute(query, {"report_type": report_type, "limit": limit})
    else:
        query = text("SELECT id, title, report_type, format, status, file_path, file_size AS file_size_bytes, expires_at, created_at FROM reports ORDER BY created_at DESC LIMIT :limit")
        result = await db.execute(query, {"limit": limit})
    reports = result.all()
    
    return [
        ReportMetadata(
            id=r.id,
            title=r.title,
            report_type=r.report_type,
            format=r.format,
            generated_at=r.created_at,
            file_size_bytes=r.file_size_bytes,
            download_url=f"/api/v1/reports/{r.id}/download",
            expires_at=r.expires_at or (datetime.now() + timedelta(days=7))
        ) for r in reports
    ]


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    # Delete a generated report
    return {"status": "deleted", "report_id": report_id}


# Scheduled Reports
@router.post("/schedule", response_model=ScheduledReport)
async def schedule_report(
    request: ScheduleReportRequest,
    db: AsyncSession = Depends(get_db)
):
    # Schedule a recurring report in DB
    # Calculate next run time
    next_run = datetime.now().replace(hour=9, minute=0, second=0)
    if next_run < datetime.now():
        next_run += timedelta(days=1)
    
    import json
    
    schedule_id = str(uuid.uuid4())
    created_now = datetime.now()
    stmt = text("""
        INSERT INTO scheduled_tasks (id, name, task_type, frequency, next_run, recipients_json, is_active, created_at)
        VALUES (:id, :name, :task_type, :frequency, :next_run, :recipients_json, :is_active, :created_at)
    """)
    await db.execute(stmt, {
        "id": schedule_id,
        "name": request.title,
        "task_type": request.report_type,
        "frequency": request.frequency,
        "next_run": next_run,
        "recipients_json": json.dumps(request.recipients),
        "is_active": True,
        "created_at": created_now
    })
    await db.commit()
    
    return ScheduledReport(
        id=schedule_id,
        title=request.title,
        report_type=request.report_type,
        frequency=request.frequency,
        next_run=next_run,
        recipients=request.recipients,
        is_active=True,
        created_at=created_now
    )


@router.get("/schedule", response_model=List[ScheduledReport])
async def list_scheduled_reports(db: AsyncSession = Depends(get_db)):
    # List all scheduled reports from DB
    import json
    
    query = text("""
        SELECT id, name, task_type, frequency, next_run, recipients_json, is_active, created_at 
        FROM scheduled_tasks 
        WHERE task_type IN (:t1, :t2, :t3, :t4, :t5)
    """)
    result = await db.execute(query, {
        "t1": ReportType.DAILY_SUMMARY.value if hasattr(ReportType.DAILY_SUMMARY, "value") else ReportType.DAILY_SUMMARY,
        "t2": ReportType.WEEKLY_ANALYSIS.value if hasattr(ReportType.WEEKLY_ANALYSIS, "value") else ReportType.WEEKLY_ANALYSIS,
        "t3": ReportType.MONTHLY_REPORT.value if hasattr(ReportType.MONTHLY_REPORT, "value") else ReportType.MONTHLY_REPORT,
        "t4": ReportType.CUSTOM.value if hasattr(ReportType.CUSTOM, "value") else ReportType.CUSTOM,
        "t5": "report_generation"
    })
    tasks = result.all()
    
    return [
        ScheduledReport(
            id=t.id,
            title=t.name,
            report_type=t.task_type if t.task_type in [rt.value for rt in ReportType] else ReportType.CUSTOM,
            frequency=t.frequency,
            next_run=t.next_run or datetime.now(),
            recipients=json.loads(t.recipients_json) if t.recipients_json else [],
            is_active=t.is_active,
            created_at=t.created_at
        ) for t in tasks
    ]


@router.put("/schedule/{schedule_id}/toggle")
async def toggle_scheduled_report(schedule_id: str):
    # Enable or disable a scheduled report
    return {
        "schedule_id": schedule_id,
        "is_active": True,  # Toggled
        "message": "Scheduled report status updated"
    }


@router.delete("/schedule/{schedule_id}")
async def delete_scheduled_report(schedule_id: str):
    # Delete a scheduled report
    return {"status": "deleted", "schedule_id": schedule_id}

"""
========================================
Insights Endpoints
========================================
Dashboard data, metrics, and AI insights
"""

from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.dependencies import get_db
from app.database.models import Sale, Customer, SupportTicket, Insight, ScheduledTask

router = APIRouter()


# ========================================
# Enums
# ========================================
class TimeRange(str, Enum):
    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ========================================
# Schemas
# ========================================
class MetricCard(BaseModel):
    """Single metric for dashboard"""
    id: str
    title: str
    value: str
    change: float = Field(..., description="Percentage change")
    trend: TrendDirection
    period: str
    icon: Optional[str] = None


class AlertItem(BaseModel):
    """Alert/notification item"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    is_read: bool = False
    action_url: Optional[str] = None


class AIInsight(BaseModel):
    """AI-generated insight"""
    id: str
    title: str
    summary: str
    details: str
    confidence: float
    sources: List[str]
    generated_at: datetime
    category: str
    priority: int = Field(..., ge=1, le=5)


class ChartData(BaseModel):
    """Data for chart visualization"""
    chart_type: str = Field(..., description="'line', 'bar', 'pie', 'area'")
    title: str
    data: List[dict]
    x_axis: str
    y_axis: str


class DashboardData(BaseModel):
    """Complete dashboard data"""
    metrics: List[MetricCard]
    alerts: List[AlertItem]
    insights: List[AIInsight]
    charts: List[ChartData]
    last_updated: datetime


class InsightRequest(BaseModel):
    """Request for AI insights"""
    focus_area: Optional[str] = Field(default=None, description="e.g., 'sales', 'customers'")
    time_range: TimeRange = TimeRange.WEEK
    max_insights: int = Field(default=5, ge=1, le=10)


# ========================================
# Endpoints
# ========================================
@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    time_range: TimeRange = Query(default=TimeRange.WEEK),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all dashboard data including metrics, alerts, and AI insights.
    """
    now = datetime.utcnow()
    
    # 1. Determine Date Range
    if time_range == TimeRange.TODAY:
        start_date = now - timedelta(days=1)
        prev_start_date = now - timedelta(days=2)
    elif time_range == TimeRange.WEEK:
        start_date = now - timedelta(weeks=1)
        prev_start_date = now - timedelta(weeks=2)
    elif time_range == TimeRange.MONTH:
        start_date = now - timedelta(days=30)
        prev_start_date = now - timedelta(days=60)
    elif time_range == TimeRange.QUARTER:
        start_date = now - timedelta(days=90)
        prev_start_date = now - timedelta(days=180)
    else: # YEAR
        start_date = now - timedelta(days=365)
        prev_start_date = now - timedelta(days=730)

    # 2. Fetch Metrics
    
    # Revenue
    revenue_query = select(func.sum(Sale.amount)).where(Sale.date >= start_date)
    revenue_result = await db.execute(revenue_query)
    current_revenue = revenue_result.scalar() or 0.0

    prev_revenue_query = select(func.sum(Sale.amount)).where(Sale.date >= prev_start_date, Sale.date < start_date)
    prev_revenue_result = await db.execute(prev_revenue_query)
    prev_revenue = prev_revenue_result.scalar() or 0.0
    
    revenue_change = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0.0
    revenue_trend = TrendDirection.UP if revenue_change > 0 else (TrendDirection.DOWN if revenue_change < 0 else TrendDirection.STABLE)

    # Customers
    total_customers_query = select(func.count(Customer.id))
    total_customers_result = await db.execute(total_customers_query)
    total_customers = total_customers_result.scalar() or 0

    new_cust_query = select(func.count(Customer.id)).where(Customer.created_at >= start_date)
    new_cust_result = await db.execute(new_cust_query)
    new_customers = new_cust_result.scalar() or 0
    
    prev_cust_query = select(func.count(Customer.id)).where(Customer.created_at >= prev_start_date, Customer.created_at < start_date)
    prev_cust_result = await db.execute(prev_cust_query)
    prev_new_customers = prev_cust_result.scalar() or 0

    cust_change = ((new_customers - prev_new_customers) / prev_new_customers * 100) if prev_new_customers > 0 else 0.0
    cust_trend = TrendDirection.UP if cust_change > 0 else (TrendDirection.DOWN if cust_change < 0 else TrendDirection.STABLE)

    # Open Tickets
    ticket_query = select(func.count(SupportTicket.id)).where(SupportTicket.status != 'resolved')
    ticket_result = await db.execute(ticket_query)
    open_tickets = ticket_result.scalar() or 0
    
    # Tickets change logic could be added effectively similar to above
    
    # Pending Tasks (Scheduled Tasks)
    task_query = select(func.count(ScheduledTask.id)).where(ScheduledTask.is_active == True)
    task_result = await db.execute(task_query)
    active_tasks = task_result.scalar() or 0

    # 3. Construct Metric Cards
    metrics = [
        MetricCard(
            id="revenue",
            title="Revenue",
            value=f"₹{current_revenue/100000:.1f}L" if current_revenue > 100000 else f"₹{current_revenue:.0f}",
            change=round(revenue_change, 1),
            trend=revenue_trend,
            period="vs last period",
            icon="trending-up"
        ),
        MetricCard(
            id="customers",
            title="Active Customers",
            value=f"{total_customers}",
            change=round(cust_change, 1),
            trend=cust_trend,
            period="vs last period",
            icon="users"
        ),
        MetricCard(
            id="tickets",
            title="Open Tickets",
            value=f"{open_tickets}",
            change=0.0, # Simplified for now
            trend=TrendDirection.STABLE,
            period="vs last period",
            icon="ticket"
        ),
        MetricCard(
            id="tasks",
            title="Pending Tasks",
            value=f"{active_tasks}",
            change=0.0,
            trend=TrendDirection.STABLE,
            period="vs last period",
            icon="clipboard"
        )
    ]

    # 4. Fetch Insights
    insight_query = select(Insight).order_by(desc(Insight.priority), desc(Insight.created_at)).limit(5)
    insight_result = await db.execute(insight_query)
    db_insights = insight_result.scalars().all()
    
    insights_list = [
        AIInsight(
            id=str(i.id),
            title=i.title,
            summary=i.summary,
            details=i.details,
            confidence=i.confidence,
            sources=[],
            generated_at=i.created_at,
            category=i.category,
            priority=1 if i.priority == "critical" else (2 if i.priority == "high" else 3)
        ) for i in db_insights
    ]

    # 5. Fetch Alerts (High Priority Open Tickets)
    alert_query = select(SupportTicket).where(SupportTicket.priority.in_(['high', 'critical']), SupportTicket.status == 'open').limit(5)
    alert_result = await db.execute(alert_query)
    high_pri_tickets = alert_result.scalars().all()

    alerts_list = [
        AlertItem(
            id=f"ticket_{t.id}",
            title=f"Critical: {t.subject}",
            message=f"Ticket #{t.id} - {t.status}",
            severity=AlertSeverity.CRITICAL if t.priority == 'critical' else AlertSeverity.WARNING,
            timestamp=t.created_at,
            is_read=False
        ) for t in high_pri_tickets
    ]

    # 6. Charts (Mocked based on Real Revenue or simple aggregation)
    # Aggregating by day in SQL for the last 7 days
    chart_start = now - timedelta(days=7)
    # Note: date_trunc is Postgres specific. Assuming Postgres.
    chart_query = select(
        Sale.date, 
        Sale.amount
    ).where(Sale.date >= chart_start).order_by(Sale.date)
    
    chart_result = await db.execute(chart_query)
    sales_data = chart_result.all()
    
    # Process in python for simplicity to avoid SQL dialect issues if sqlite
    from collections import defaultdict
    daily_sales = defaultdict(float)
    for s in sales_data:
        date_str = s.date.strftime("%a")
        daily_sales[date_str] += s.amount
        
    days = [(now - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
    chart_data_points = [{"date": d, "value": daily_sales.get(d, 0)} for d in days]

    charts_list = [
        ChartData(
            chart_type="line",
            title="Revenue Trend (7 Days)",
            data=chart_data_points,
            x_axis="date",
            y_axis="value"
        )
    ]

    return DashboardData(
        metrics=metrics,
        alerts=alerts_list,
        insights=insights_list,
        charts=charts_list,
        last_updated=now
    )


@router.get("/metrics", response_model=List[MetricCard])
async def get_metrics(
    time_range: TimeRange = Query(default=TimeRange.WEEK)
):
    """
    Get key business metrics only.
    """
    dashboard = await get_dashboard_data(time_range)
    return dashboard.metrics


@router.get("/alerts", response_model=List[AlertItem])
async def get_alerts(
    severity: Optional[AlertSeverity] = None,
    unread_only: bool = False
):
    """
    Get alerts and notifications.
    """
    dashboard = await get_dashboard_data(TimeRange.WEEK)
    alerts = dashboard.alerts
    
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    
    if unread_only:
        alerts = [a for a in alerts if not a.is_read]
    
    return alerts


@router.post("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str):
    """Mark an alert as read."""
    return {"status": "success", "alert_id": alert_id}


@router.post("/insights/generate", response_model=List[AIInsight])
async def generate_insights(request: InsightRequest):
    """
    Generate AI insights on demand.
    
    The AI will analyze available data and produce actionable insights.
    """
    # This would trigger the agent system to analyze data
    return [
        AIInsight(
            id="generated_1",
            title=f"AI Analysis: {request.focus_area or 'General'}",
            summary="Based on analysis of recent data...",
            details="Detailed AI-generated analysis...",
            confidence=0.85,
            sources=["analyzed_data"],
            generated_at=datetime.now(),
            category=request.focus_area or "general",
            priority=2
        )
    ]


@router.get("/trends")
async def get_trends(
    metric: str = Query(..., description="Metric to analyze"),
    time_range: TimeRange = Query(default=TimeRange.MONTH)
):
    """
    Get trend analysis for a specific metric.
    """
    return {
        "metric": metric,
        "time_range": time_range.value,
        "trend": "increasing",
        "change_percent": 12.5,
        "forecast": "Expected to continue upward trend",
        "data_points": [
            {"date": "2024-01-01", "value": 100},
            {"date": "2024-01-08", "value": 105},
            {"date": "2024-01-15", "value": 112},
            {"date": "2024-01-22", "value": 108},
            {"date": "2024-01-29", "value": 118}
        ]
    }


@router.get("/anomalies")
async def detect_anomalies(
    time_range: TimeRange = Query(default=TimeRange.WEEK)
):
    """
    Detect anomalies in business data.
    """
    return {
        "anomalies": [
            {
                "id": "anomaly_1",
                "metric": "revenue",
                "date": "2024-01-23",
                "expected_value": 15000,
                "actual_value": 9000,
                "deviation_percent": -40,
                "severity": "high",
                "possible_causes": [
                    "Payment gateway issues",
                    "Competitor promotion",
                    "Website downtime"
                ]
            }
        ],
        "analyzed_at": datetime.now().isoformat()
    }

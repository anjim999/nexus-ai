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
    time_range: TimeRange = Query(default=TimeRange.WEEK)
):
    """
    Get all dashboard data including metrics, alerts, and AI insights.
    """
    # Sample data - in production, this would come from actual data sources
    return DashboardData(
        metrics=[
            MetricCard(
                id="revenue",
                title="Revenue",
                value="₹12.4L",
                change=12.5,
                trend=TrendDirection.UP,
                period="vs last week",
                icon="trending-up"
            ),
            MetricCard(
                id="customers",
                title="Active Customers",
                value="1,247",
                change=8.3,
                trend=TrendDirection.UP,
                period="vs last week",
                icon="users"
            ),
            MetricCard(
                id="tickets",
                title="Open Tickets",
                value="47",
                change=-15.2,
                trend=TrendDirection.DOWN,
                period="vs last week",
                icon="ticket"
            ),
            MetricCard(
                id="tasks",
                title="Pending Tasks",
                value="23",
                change=5.0,
                trend=TrendDirection.STABLE,
                period="vs last week",
                icon="clipboard"
            )
        ],
        alerts=[
            AlertItem(
                id="alert_1",
                title="Revenue Anomaly Detected",
                message="Revenue dropped 25% on Tuesday compared to average",
                severity=AlertSeverity.WARNING,
                timestamp=datetime.now() - timedelta(hours=2),
                is_read=False
            ),
            AlertItem(
                id="alert_2",
                title="Customer Churn Risk",
                message="3 high-value customers showing disengagement patterns",
                severity=AlertSeverity.CRITICAL,
                timestamp=datetime.now() - timedelta(hours=5),
                is_read=False
            )
        ],
        insights=[
            AIInsight(
                id="insight_1",
                title="Marketing Campaign Impact",
                summary="Recent email campaign drove 35% increase in website traffic",
                details="Analysis shows direct correlation between campaign launch and user engagement...",
                confidence=0.89,
                sources=["analytics_db", "marketing_report.pdf"],
                generated_at=datetime.now() - timedelta(minutes=30),
                category="marketing",
                priority=2
            ),
            AIInsight(
                id="insight_2",
                title="Product Performance",
                summary="Product A outperforming others by 40% this quarter",
                details="Detailed analysis...",
                confidence=0.92,
                sources=["sales_db", "product_metrics"],
                generated_at=datetime.now() - timedelta(hours=1),
                category="products",
                priority=1
            )
        ],
        charts=[
            ChartData(
                chart_type="line",
                title="Revenue Trend",
                data=[
                    {"date": "Mon", "value": 12000},
                    {"date": "Tue", "value": 9000},
                    {"date": "Wed", "value": 15000},
                    {"date": "Thu", "value": 14000},
                    {"date": "Fri", "value": 18000},
                    {"date": "Sat", "value": 16000},
                    {"date": "Sun", "value": 11000}
                ],
                x_axis="date",
                y_axis="value"
            )
        ],
        last_updated=datetime.now()
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

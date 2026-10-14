"""
Reports & Analytical Dashboard API Router:
Aggregates sales performance, conversion velocities, and receivables breakdown.
"""
from typing import Optional
from datetime import date
from fastapi import APIRouter, Query

from app.services.report_service import ReportService

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_metrics(timeframe: str = Query("Monthly", description="Daily, Weekly, Monthly, or All")):
    """Returns real-time KPI metrics for dashboard cards and mobile overview."""
    metrics = ReportService.get_dashboard_metrics(timeframe=timeframe)
    today = date.today()
    try:
        team_data = ReportService.get_team_target_performance(today.year, today.month)
        reps_list = team_data.get("individual_performance", [])
    except Exception:
        team_data = {}
        reps_list = []

    res = dict(metrics)
    res["kpis"] = {
        "won_amount": metrics.get("won_sales_value", 0.0),
        "open_amount": metrics.get("pipeline_value", 0.0),
        "total_count": metrics.get("total_quotes", 0),
        "conversion_rate": metrics.get("conversion_rate", 0.0),
        "cleared_payments": metrics.get("cleared_payments", 0.0),
        "total_outstanding": metrics.get("total_outstanding", 0.0),
    }
    res["sales_reps"] = reps_list
    res["team_target"] = team_data.get("team_target", 0.0)
    res["team_achieved"] = team_data.get("team_achieved", 0.0)
    return res


@router.get("/daily")
def get_daily_report(report_date: Optional[str] = Query(None, description="YYYY-MM-DD")):
    """Retrieves audit report data for a specific day."""
    d = report_date or date.today().strftime("%Y-%m-%d")
    data = ReportService.get_daily_report_data(d)
    return data


@router.get("/monthly")
def get_monthly_report(year: Optional[int] = Query(None), month: Optional[int] = Query(None)):
    """Retrieves audit report data for a specific calendar month."""
    today = date.today()
    y = year or today.year
    m = month or today.month
    data = ReportService.get_monthly_report_data(y, m)
    return data


@router.get("/target-archive")
def get_target_archive():
    """Retrieves historical target archive audit data."""
    data = ReportService.get_target_archive_data()
    return data

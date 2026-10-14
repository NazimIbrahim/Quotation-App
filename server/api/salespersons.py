"""
Sales Team & Target Analytics API Router:
Provides salesperson profiles, monthly targets, sales achieved, and pipeline attribution.
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.database.models import SalesPerson

router = APIRouter()


@router.get("")
def list_salespersons(year: Optional[int] = Query(None), month: Optional[int] = Query(None)):
    """Lists all active sales associates and managers with target achievement metrics."""
    today = date.today()
    y = year or today.year
    m = month or today.month

    team = SalesPerson.select().where(SalesPerson.is_active == True).order_by(SalesPerson.name)
    results = []

    for sp in team:
        target = float(sp.get_target_for_month(y, m))
        achieved = float(sp.get_sales_achieved(month=m, year=y))
        pipeline = float(sp.get_pipeline_value(month=m, year=y))
        pct = round((achieved / target * 100.0), 1) if target > 0 else 100.0

        results.append({
            "id": sp.id,
            "name": sp.name,
            "role": sp.role,
            "phone": sp.contact_number,
            "email": sp.email,
            "monthly_target": target,
            "sales_achieved": achieved,
            "pipeline_value": pipeline,
            "percentage_achieved": pct,
        })

    return {"count": len(results), "sales_team": results}


@router.get("/{sp_id}")
def get_salesperson(sp_id: int):
    """Retrieves salesperson details."""
    sp = SalesPerson.get_or_none(SalesPerson.id == sp_id)
    if not sp:
        raise HTTPException(status_code=404, detail="Salesperson not found")

    today = date.today()
    return {
        "id": sp.id,
        "name": sp.name,
        "role": sp.role,
        "phone": sp.contact_number,
        "email": sp.email,
        "monthly_target": float(sp.monthly_target),
        "achieved_current_month": float(sp.get_sales_achieved(month=today.month, year=today.year)),
        "pipeline_current_month": float(sp.get_pipeline_value(month=today.month, year=today.year)),
    }

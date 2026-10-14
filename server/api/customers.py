"""
Customers API Router:
Handles listing, real-time search, profile lookup, creation, and updates for customers.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from peewee import fn

from app.database.models import Customer, Quotation

router = APIRouter()


class CustomerPayload(BaseModel):
    name: str
    mobile_number: Optional[str] = None
    phone: Optional[str] = None
    delivery_address: Optional[str] = ""
    email: Optional[str] = None
    site_location: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
def list_customers(search: Optional[str] = Query(None, description="Search name, phone, or location")):
    """Searches customers by phone, name, or location with quote count and total won value."""
    query = Customer.select().order_by(Customer.name)
    if search:
        pat = f"%{search.strip()}%"
        query = query.where(
            (Customer.name.ilike(pat)) |
            (Customer.mobile_number.ilike(pat)) |
            (Customer.delivery_address.ilike(pat)) |
            (Customer.site_location.ilike(pat))
        )

    cust_list = list(query)
    if not cust_list:
        return {"count": 0, "customers": []}

    # Batch quote counts
    c_ids = [c.id for c in cust_list]
    counts_map = dict(
        Quotation.select(Quotation.customer_id, fn.COUNT(Quotation.id))
        .where(Quotation.customer_id.in_(c_ids))
        .group_by(Quotation.customer_id)
        .tuples()
    )

    results = []
    for c in cust_list:
        results.append({
            "id": c.id,
            "name": c.name,
            "mobile_number": c.mobile_number,
            "phone": c.mobile_number,
            "delivery_address": c.delivery_address,
            "email": c.email,
            "site_location": c.site_location,
            "notes": c.notes,
            "quote_count": counts_map.get(c.id, 0),
            "total_quotations": counts_map.get(c.id, 0),
            "total_won_value": float(c.get_total_won_value() or 0.0),
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(c.created_at, "strftime") else str(c.created_at)
        })

    return {"count": len(results), "customers": results}


@router.get("/{customer_id}")
def get_customer(customer_id: int):
    """Retrieves customer profile and full history of quotations."""
    customer = Customer.get_or_none(Customer.id == customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    quotes = Quotation.select().where(Quotation.customer == customer).order_by(Quotation.id.desc())
    quote_history = []
    for q in quotes:
        quote_history.append({
            "id": q.id,
            "quotation_number": q.quotation_number,
            "quotation_date": q.quotation_date.strftime("%Y-%m-%d") if hasattr(q.quotation_date, "strftime") else str(q.quotation_date),
            "status": q.status,
            "net_total": float(q.net_total or 0.0),
            "cleared_payments": float(q.get_cleared_payments() or 0.0),
            "outstanding_balance": float(q.get_outstanding_balance() or 0.0),
        })

    return {
        "id": customer.id,
        "name": customer.name,
        "mobile_number": customer.mobile_number,
        "delivery_address": customer.delivery_address,
        "email": customer.email,
        "site_location": customer.site_location,
        "notes": customer.notes,
        "total_won_value": float(customer.get_total_won_value() or 0.0),
        "quotations": quote_history
    }


@router.post("")
def create_customer(payload: CustomerPayload):
    """Creates a new customer record."""
    try:
        cust = Customer.create(
            name=payload.name.strip(),
            mobile_number=payload.mobile_number.strip(),
            delivery_address=payload.delivery_address.strip(),
            email=payload.email.strip() if payload.email else None,
            site_location=payload.site_location.strip() if payload.site_location else None,
            notes=payload.notes.strip() if payload.notes else None,
        )
        return {"success": True, "id": cust.id, "name": cust.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create customer: {str(e)}")


@router.put("/{customer_id}")
def update_customer(customer_id: int, payload: CustomerPayload):
    """Updates existing customer profile."""
    customer = Customer.get_or_none(Customer.id == customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    try:
        customer.name = payload.name.strip()
        customer.mobile_number = payload.mobile_number.strip()
        customer.delivery_address = payload.delivery_address.strip()
        customer.email = payload.email.strip() if payload.email else None
        customer.site_location = payload.site_location.strip() if payload.site_location else None
        customer.notes = payload.notes.strip() if payload.notes else None
        customer.save()
        return {"success": True, "id": customer.id, "name": customer.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update customer: {str(e)}")

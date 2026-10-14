"""
Payments Tracking API Router:
Handles recording customer advances, payment clearances (GPay, PhonePe, NEFT, Cheque),
and outstanding balance audits.
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.database.models import Payment, Quotation
from app.services.payment_service import PaymentService

router = APIRouter()


class PaymentCreatePayload(BaseModel):
    quotation_id: int
    amount: float
    payment_mode: str = "UPI (Google Pay / PhonePe)"
    payment_date: Optional[str] = None
    transaction_ref: Optional[str] = None
    bank_name: Optional[str] = None
    cheque_number: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = Payment.STATUS_CLEARED


@router.get("")
def list_payments(
    quotation_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None)
):
    """Lists payments with optional filtering by quotation ID and clearance status."""
    query = Payment.select().order_by(Payment.payment_date.desc(), Payment.id.desc())
    if quotation_id:
        query = query.where(Payment.quotation_id == quotation_id)
    if status and status != "All":
        query = query.where(Payment.status == status)

    results = []
    for p in query:
        q = p.quotation
        results.append({
            "id": p.id,
            "quotation_id": p.quotation_id,
            "quotation_number": q.quotation_number if q else "",
            "customer_name": q.customer_name if q else "",
            "amount": float(p.amount),
            "payment_date": p.payment_date.strftime("%Y-%m-%d") if hasattr(p.payment_date, "strftime") else str(p.payment_date),
            "payment_mode": p.payment_mode,
            "status": p.status,
            "transaction_ref": p.transaction_ref,
            "bank_name": p.bank_name,
            "cheque_number": p.cheque_number,
            "notes": p.notes,
        })

    return {"count": len(results), "payments": results}


@router.post("")
def record_payment(payload: PaymentCreatePayload):
    """Records a new customer payment/advance against a quotation."""
    quote = Quotation.get_or_none(Quotation.id == payload.quotation_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")

    try:
        p_date = payload.payment_date or date.today().strftime("%Y-%m-%d")
        payment = PaymentService.record_payment(
            quote_id=payload.quotation_id,
            amount=payload.amount,
            mode=payload.payment_mode,
            pay_date=p_date,
            tx_ref=payload.transaction_ref,
            bank=payload.bank_name,
            cheque=payload.cheque_number,
            notes=payload.notes,
            status=payload.status or Payment.STATUS_CLEARED
        )
        return {
            "success": True,
            "id": payment.id,
            "amount": payment.amount,
            "status": payment.status,
            "quotation_net": quote.net_total,
            "cleared_now": quote.get_cleared_payments(),
            "remaining_balance": quote.get_outstanding_balance()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to record payment: {str(e)}")


@router.put("/{payment_id}/clear")
def clear_payment(payment_id: int):
    """Clears a pending payment (e.g. cheque or transfer confirmation)."""
    payment = Payment.get_or_none(Payment.id == payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.status = Payment.STATUS_CLEARED
    payment.save()
    return {"success": True, "id": payment.id, "status": payment.status}

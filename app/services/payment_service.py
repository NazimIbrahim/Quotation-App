"""
Payment Service: Manage incoming payments against quotations,
payment clearance, modes, and outstanding balances.
"""
from datetime import date, datetime
from peewee import fn
from app.database.connection import db
from app.database.models import Payment, Quotation


class PaymentService:
    @staticmethod
    def add_payment(quotation_id: int, amount: float, mode: str, payment_date: date = None,
                    status: str = Payment.STATUS_CLEARED, reference_number: str = None,
                    notes: str = None) -> Payment:
        """Records a new payment entry against a quotation."""
        quote = Quotation.get_by_id(quotation_id)
        
        payment = Payment.create(
            quotation=quote,
            amount=round(float(amount), 2),
            payment_mode=mode,
            payment_date=payment_date or date.today(),
            status=status,
            reference_number=reference_number or "",
            notes=notes or "",
        )
        return payment

    @staticmethod
    def get_payments_for_quotation(quotation_id: int):
        """Returns all payments for a given quotation."""
        return list(
            Payment.select()
            .where(Payment.quotation_id == quotation_id)
            .order_by(Payment.payment_date.desc(), Payment.id.desc())
        )

    @staticmethod
    def update_payment_status(payment_id: int, new_status: str) -> Payment:
        """Updates clearance status (Pending <-> Cleared)."""
        pmt = Payment.get_by_id(payment_id)
        pmt.status = new_status
        pmt.save()
        return pmt

    @staticmethod
    def delete_payment(payment_id: int) -> bool:
        """Deletes a payment entry."""
        pmt = Payment.get_by_id(payment_id)
        pmt.delete_instance()
        return True

    @staticmethod
    def get_financial_summary(quotation_id: int) -> dict:
        """Calculates cleared, pending, and outstanding balance for a quotation."""
        quote = Quotation.get_by_id(quotation_id)
        cleared = quote.get_cleared_payments()
        pending = quote.get_pending_payments()
        balance = quote.get_outstanding_balance()
        
        return {
            "net_total": quote.net_total,
            "cleared_amount": cleared,
            "pending_amount": pending,
            "outstanding_balance": balance,
            "payment_status": quote.get_payment_status(),
        }

    @staticmethod
    def get_overall_receivables_summary():
        """Calculates global total receivables, cleared receipts, and pending amounts."""
        # Total won or active quotation net
        total_won = (
            Quotation.select(fn.SUM(Quotation.net_total))
            .where(Quotation.status == Quotation.STATUS_WON)
            .scalar() or 0.0
        )
        
        total_active_pipeline = (
            Quotation.select(fn.SUM(Quotation.net_total))
            .where(Quotation.status.in_([Quotation.STATUS_OPEN, Quotation.STATUS_IN_REVIEW]))
            .scalar() or 0.0
        )

        cleared_received = (
            Payment.select(fn.SUM(Payment.amount))
            .where(Payment.status == Payment.STATUS_CLEARED)
            .scalar() or 0.0
        )

        pending_cheques_upi = (
            Payment.select(fn.SUM(Payment.amount))
            .where(Payment.status == Payment.STATUS_PENDING)
            .scalar() or 0.0
        )

        # Outstanding on won orders
        won_outstanding = max(0.0, total_won - cleared_received)

        return {
            "total_won": float(total_won),
            "total_active_pipeline": float(total_active_pipeline),
            "cleared_received": float(cleared_received),
            "pending_cheques_upi": float(pending_cheques_upi),
            "won_outstanding": float(won_outstanding),
        }

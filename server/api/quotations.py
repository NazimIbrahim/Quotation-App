"""
Quotations API Router:
Handles listing, creation, updates, status changes, PDF exports,
and filtered reports for quotations.
"""
import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.database.models import Quotation, QuotationArea, QuotationItem, SalesPerson, Customer
from app.services.quotation_service import QuotationService
from app.services.pdf_service import CeramicPDFGenerator
from app.services.report_pdf_service import ReportPDFGenerator
from app.services.report_service import ReportService

router = APIRouter()


class QuotationItemPayload(BaseModel):
    id: Optional[int] = None
    sl_no: Optional[int] = 1
    description: Optional[str] = "AMA Signature Ceramic Tile"
    size: Optional[str] = "600X1200"
    brand: Optional[str] = "AMA Signature Collection"
    product_type: Optional[str] = "Box"
    coverage_area: Optional[float] = 15.5
    quantity_sqft: Optional[float] = 0.0
    rate_per_sqft: Optional[float] = 0.0
    quantity_boxes: Optional[float] = 1.0
    rate_per_box: Optional[float] = 1000.0
    tax_mode: Optional[str] = "exclusive"
    tax_percent: Optional[float] = 18.0
    taxable_amount: Optional[float] = 1000.0
    gst_amount: Optional[float] = 180.0
    total_amount: Optional[float] = 1180.0


class QuotationAreaPayload(BaseModel):
    id: Optional[int] = None
    area_name: str = "General Supply"
    display_order: Optional[int] = 1
    items: List[QuotationItemPayload] = []


class QuotationSavePayload(BaseModel):
    id: Optional[int] = None
    quotation_number: Optional[str] = None
    quotation_date: Optional[str] = None
    customer_id: int
    sales_person_id: int
    project_name: Optional[str] = None
    special_notes: Optional[str] = None
    tax_mode: Optional[str] = "exclusive"
    round_off: Optional[float] = 0.0
    # Assisted Deal Collaboration
    assisted_by_id: Optional[int] = None
    split_type: Optional[str] = "none"
    assisted_share_value: Optional[float] = 0.0
    # Line Items
    areas: List[QuotationAreaPayload] = []


@router.get("")
def list_quotations(
    status: Optional[str] = Query(None, description="Filter: Won, Open, In-Review, Lost, or All"),
    sales_person_id: Optional[int] = Query(None, description="Salesperson ID"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    search: Optional[str] = Query(None, description="Search quote #, customer, phone")
):
    """Fetches list of quotations with flexible filtering for desktop and mobile clients."""
    quotes = QuotationService.get_all_quotations(
        status=status,
        sales_person_id=sales_person_id,
        search_query=search,
        start_date=start_date,
        end_date=end_date
    )

    results = []
    for q in quotes:
        results.append({
            "id": q.id,
            "quotation_number": q.quotation_number,
            "quotation_date": q.quotation_date.strftime("%Y-%m-%d") if hasattr(q.quotation_date, "strftime") else str(q.quotation_date),
            "customer_id": q.customer_id,
            "customer_name": q.customer_name,
            "customer_phone": q.customer_phone,
            "delivery_address": q.delivery_address,
            "sales_person_id": q.sales_person_id,
            "sales_person_name": q.sales_person_name,
            "assisted_by_id": getattr(q, "assisted_by_id", None),
            "assisted_by_name": getattr(q, "assisted_by_name", None),
            "split_type": getattr(q, "split_type", "none"),
            "status": q.status,
            "tax_mode": getattr(q, "tax_mode", "exclusive"),
            "taxable_amount": float(q.taxable_amount or 0.0),
            "total_tax": float(q.total_tax or 0.0),
            "gross_total": float(q.gross_total or 0.0),
            "net_total": float(q.net_total or 0.0),
            "cleared_payments": float(q.get_cleared_payments() or 0.0),
            "outstanding_balance": float(q.get_outstanding_balance() or 0.0),
            "payment_status": q.get_payment_status(),
        })

    return {"count": len(results), "quotations": results}


@router.get("/{quote_id}")
def get_quotation(quote_id: int):
    """Retrieves full quotation structure including areas, items, and payments."""
    details = QuotationService.get_quotation_details(quote_id)
    if not details:
        raise HTTPException(status_code=404, detail="Quotation not found")
    res = dict(details)
    res["quotation"] = details
    return res


@router.post("")
def save_quotation(payload: QuotationSavePayload):
    """Creates a new quotation or updates an existing quotation."""
    try:
        quote = QuotationService.save_quotation(payload.model_dump())
        return {
            "success": True,
            "id": quote.id,
            "quotation_number": quote.quotation_number,
            "net_total": quote.net_total,
            "status": quote.status,
            "message": "Quotation saved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save quotation: {str(e)}")


@router.delete("/{quote_id}")
def delete_quotation(quote_id: int):
    """Deletes quotation by ID."""
    success = QuotationService.delete_quotation(quote_id)
    if not success:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return {"success": True, "message": f"Quotation {quote_id} deleted"}


@router.put("/{quote_id}/status")
def update_status(quote_id: int, status: str = Query(...), note: Optional[str] = Query(None)):
    """Updates quotation status (Won, Open, In-Review, Lost)."""
    quote = QuotationService.update_status(quote_id, status, note=note)
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return {"success": True, "id": quote.id, "status": quote.status}


@router.get("/{quote_id}/pdf")
def get_quotation_pdf(quote_id: int, encrypted: bool = Query(False, description="Export with masked AMA product codes")):
    """Generates and serves high-resolution quotation PDF for mobile view, download, or WhatsApp sharing."""
    quote = Quotation.get_or_none(Quotation.id == quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")

    try:
        pdf_path = CeramicPDFGenerator.generate_quotation_pdf(quote_id, encrypted=encrypted)
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF generation failed")

        filename = os.path.basename(pdf_path)
        return FileResponse(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")


@router.get("/export/report")
def export_quotation_report(
    format: str = Query("pdf", description="pdf or csv"),
    status: Optional[str] = Query(None),
    sales_person_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Exports itemized quotations audit report as PDF or CSV."""
    try:
        if format.lower() == "csv":
            csv_path = ReportService.export_quotations_csv(
                start_date=start_date,
                end_date=end_date,
                sales_person_id=sales_person_id,
                status=status
            )
            return FileResponse(path=csv_path, filename=os.path.basename(csv_path), media_type="text/csv")
        else:
            pdf_path = ReportPDFGenerator.generate_quotations_report_pdf(
                start_date=start_date,
                end_date=end_date,
                sales_person_id=sales_person_id,
                status=status
            )
            return FileResponse(path=pdf_path, filename=os.path.basename(pdf_path), media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report export failed: {str(e)}")

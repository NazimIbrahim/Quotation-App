"""
Quotation Service: Business logic for creating, updating, auto-numbering,
and calculating ceramic & tile quotations.
"""
from datetime import date, datetime
from peewee import fn
from app.database.connection import db
from app.database.models import (
    Quotation,
    QuotationArea,
    QuotationItem,
    Customer,
    SalesPerson,
)


class QuotationService:
    @staticmethod
    def generate_next_quotation_number() -> str:
        """Generates the next sequential quotation number: AMA-YYYY-XXXX."""
        current_year = date.today().year
        prefix = f"AMA-{current_year}-"
        
        last_quote = (
            Quotation.select()
            .where(Quotation.quotation_number.startswith(prefix))
            .order_by(Quotation.id.desc())
            .first()
        )
        
        if last_quote:
            try:
                last_num_str = last_quote.quotation_number.replace(prefix, "")
                next_seq = int(last_num_str) + 1
            except ValueError:
                next_seq = Quotation.select().count() + 1
        else:
            next_seq = Quotation.select().count() + 1
            
        return f"{prefix}{next_seq:04d}"

    @staticmethod
    def get_all_quotations(status=None, sales_person_id=None, search_query=None):
        """Fetches quotations with optional filtering."""
        query = Quotation.select().order_by(Quotation.id.desc())
        
        if status and status != "All":
            query = query.where(Quotation.status == status)
            
        if sales_person_id:
            query = query.where(Quotation.sales_person_id == sales_person_id)
            
        if search_query:
            pattern = f"%{search_query}%"
            query = query.where(
                (Quotation.quotation_number.ilike(pattern)) |
                (Quotation.customer_name.ilike(pattern)) |
                (Quotation.customer_phone.ilike(pattern)) |
                (Quotation.project_name.ilike(pattern))
            )
            
        return list(query)

    @staticmethod
    def get_quotation_by_id(quote_id: int):
        """Fetches quotation by ID with its areas and items."""
        return Quotation.get_or_none(Quotation.id == quote_id)

    @staticmethod
    def get_quotation_details(quote_id: int):
        """Returns structured dictionary of quotation including areas and line items."""
        quote = Quotation.get_or_none(Quotation.id == quote_id)
        if not quote:
            return None

        areas_data = []
        for area in quote.areas.order_by(QuotationArea.display_order):
            items_data = []
            for it in area.items.order_by(QuotationItem.sl_no):
                items_data.append({
                    "id": it.id,
                    "sl_no": it.sl_no,
                    "description": it.description,
                    "size": it.size,
                    "brand": getattr(it, "brand", ""),
                    "coverage_area": float(getattr(it, "coverage_area", 0.0) or 0.0),
                    "quantity_sqft": it.quantity_sqft,
                    "rate_per_sqft": it.rate_per_sqft,
                    "quantity_boxes": it.quantity_boxes,
                    "rate_per_box": it.rate_per_box,
                    "total_amount": it.total_amount,
                })
            areas_data.append({
                "id": area.id,
                "area_name": area.area_name,
                "display_order": area.display_order,
                "items": items_data,
            })

        return {
            "id": quote.id,
            "quotation_number": quote.quotation_number,
            "quotation_date": quote.quotation_date,
            "customer_id": quote.customer_id,
            "customer_name": quote.customer_name,
            "customer_phone": quote.customer_phone,
            "delivery_address": quote.delivery_address,
            "sales_person_id": quote.sales_person_id,
            "sales_person_name": quote.sales_person_name,
            "project_name": quote.project_name,
            "special_notes": quote.special_notes,
            "status": quote.status,
            "gross_total": quote.gross_total,
            "round_off": quote.round_off,
            "net_total": quote.net_total,
            "approved_by_id": quote.approved_by_id,
            "approved_at": quote.approved_at,
            "manager_approval_note": quote.manager_approval_note,
            "areas": areas_data,
        }

    @staticmethod
    def save_quotation(data: dict) -> Quotation:
        """
        Creates or updates a complete quotation including areas and items.
        data structure:
        {
            "id": int (optional, for update),
            "quotation_number": str,
            "quotation_date": date,
            "customer_id": int,
            "sales_person_id": int,
            "project_name": str,
            "special_notes": str,
            "status": str,
            "round_off": float,
            "areas": [
                {
                    "area_name": str,
                    "items": [
                        {
                            "description": str,
                            "size": str,
                            "quantity_sqft": float,
                            "rate_per_sqft": float,
                            "quantity_boxes": float,
                            "rate_per_box": float,
                            "total_amount": float
                        }
                    ]
                }
            ]
        }
        """
        with db.atomic():
            cust = Customer.get_by_id(data["customer_id"])
            sp = SalesPerson.get_by_id(data["sales_person_id"])

            quote_id = data.get("id")
            if quote_id:
                quote = Quotation.get_by_id(quote_id)
                quote.quotation_date = data.get("quotation_date", quote.quotation_date)
                quote.customer = cust
                quote.customer_name = cust.name
                quote.customer_phone = cust.mobile_number
                quote.delivery_address = cust.delivery_address
                quote.sales_person = sp
                quote.sales_person_name = sp.name
                quote.project_name = data.get("project_name", "")
                quote.special_notes = data.get("special_notes", "")
                quote.status = data.get("status", quote.status)
                quote.round_off = float(data.get("round_off", 0.0))
                quote.updated_at = datetime.now()
                quote.save()

                # Remove existing areas/items to replace cleanly
                QuotationItem.delete().where(QuotationItem.quotation == quote).execute()
                QuotationArea.delete().where(QuotationArea.quotation == quote).execute()
            else:
                q_num = data.get("quotation_number") or QuotationService.generate_next_quotation_number()
                quote = Quotation.create(
                    quotation_number=q_num,
                    quotation_date=data.get("quotation_date", date.today()),
                    customer=cust,
                    customer_name=cust.name,
                    customer_phone=cust.mobile_number,
                    delivery_address=cust.delivery_address,
                    sales_person=sp,
                    sales_person_name=sp.name,
                    project_name=data.get("project_name", ""),
                    special_notes=data.get("special_notes", ""),
                    status=data.get("status", Quotation.STATUS_OPEN),
                    round_off=float(data.get("round_off", 0.0)),
                    gross_total=0.0,
                    net_total=0.0,
                )

            # Insert areas and line items
            gross_total = 0.0
            global_sl = 1
            for a_idx, area_data in enumerate(data.get("areas", []), start=1):
                area_name = area_data.get("area_name", f"Area {a_idx}").strip()
                if not area_name:
                    area_name = f"Area {a_idx}"
                    
                area_obj = QuotationArea.create(
                    quotation=quote,
                    area_name=area_name,
                    display_order=a_idx
                )

                for item_data in area_data.get("items", []):
                    desc = item_data.get("description", "").strip()
                    if not desc:
                        continue
                    
                    size = item_data.get("size", "").strip()
                    brand = item_data.get("brand", "").strip()
                    coverage_area = float(item_data.get("coverage_area") or 0.0)
                    qty_sqft = float(item_data.get("quantity_sqft") or 0.0)
                    rate_sqft = float(item_data.get("rate_per_sqft") or 0.0)
                    qty_boxes = float(item_data.get("quantity_boxes") or 0.0)
                    rate_box = float(item_data.get("rate_per_box") or 0.0)
                    
                    # Calculate item total
                    item_total = float(item_data.get("total_amount") or 0.0)
                    if item_total <= 0:
                        if qty_sqft > 0 and rate_sqft > 0:
                            item_total = round(qty_sqft * rate_sqft, 2)
                        elif qty_boxes > 0 and rate_box > 0:
                            item_total = round(qty_boxes * rate_box, 2)

                    gross_total += item_total

                    QuotationItem.create(
                        area=area_obj,
                        quotation=quote,
                        sl_no=global_sl,
                        description=desc,
                        size=size,
                        brand=brand,
                        coverage_area=coverage_area,
                        quantity_sqft=qty_sqft,
                        rate_per_sqft=rate_sqft,
                        quantity_boxes=qty_boxes,
                        rate_per_box=rate_box,
                        total_amount=round(item_total, 2)
                    )
                    global_sl += 1

            quote.gross_total = round(gross_total, 2)
            quote.net_total = round(gross_total + quote.round_off, 2)
            quote.save()

            return quote

    @staticmethod
    def update_status(quote_id: int, new_status: str, manager: SalesPerson = None, note: str = None):
        """Updates quotation status and logs manager approval if applicable."""
        quote = Quotation.get_by_id(quote_id)
        quote.status = new_status
        quote.updated_at = datetime.now()
        if manager and manager.role == SalesPerson.ROLE_MANAGER:
            quote.approved_by = manager
            quote.approved_at = datetime.now()
            if note:
                quote.manager_approval_note = note
        quote.save()
        return quote

    @staticmethod
    def delete_quotation(quote_id: int):
        """Deletes quotation and cascaded items/payments."""
        quote = Quotation.get_by_id(quote_id)
        quote.delete_instance(recursive=True)
        return True

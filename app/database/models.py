"""
Database models for AMA Ceramics Quotation Management System using Peewee ORM.
"""
from datetime import datetime, date, timedelta
from peewee import (
    Model,
    CharField,
    TextField,
    FloatField,
    IntegerField,
    DateField,
    DateTimeField,
    BooleanField,
    ForeignKeyField,
    fn,
)
from app.database.connection import db


class BaseModel(Model):
    class Meta:
        database = db


class SalesPerson(BaseModel):
    """Salesperson and Manager users."""
    ROLE_SALES = "Sales Person"
    ROLE_MANAGER = "Manager"

    name = CharField(max_length=120)
    contact_number = CharField(max_length=30)
    email = CharField(max_length=120, null=True)
    role = CharField(max_length=30, default=ROLE_SALES)  # Sales Person or Manager
    monthly_target = FloatField(default=500000.0)  # Default Fallback Monthly Target Amount in INR
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "sales_persons"

    def get_target_for_month(self, year: int = None, month: int = None) -> float:
        """Returns the specific target for that calendar month if set, otherwise base monthly_target."""
        today = date.today()
        y = year or today.year
        m = month or today.month

        try:
            t = (
                SalesTarget.select()
                .where(
                    (SalesTarget.sales_person == self) &
                    (SalesTarget.target_type == SalesTarget.TARGET_MONTHLY) &
                    (SalesTarget.year == y) &
                    (SalesTarget.month == m)
                )
                .first()
            )
            if t:
                return float(t.target_amount)
        except Exception:
            pass
        return float(self.monthly_target)

    def get_target_for_period(self, start_date: date, end_date: date) -> float:
        """
        Resolves the appropriate target for any date period:
        1. Exact custom or weekly target matching start_date and end_date
        2. Monthly target if dates match a calendar month
        3. Pro-rata calculation based on month's target
        """
        try:
            # 1. Exact match
            t = (
                SalesTarget.select()
                .where(
                    (SalesTarget.sales_person == self) &
                    (SalesTarget.start_date == start_date) &
                    (SalesTarget.end_date == end_date)
                )
                .first()
            )
            if t:
                return float(t.target_amount)
        except Exception:
            pass

        # 2. Full calendar month
        if start_date.day == 1:
            next_m = date(start_date.year, start_date.month + 1, 1) if start_date.month < 12 else date(start_date.year + 1, 1, 1)
            last_day = next_m - timedelta(days=1)
            if end_date == last_day:
                return self.get_target_for_month(start_date.year, start_date.month)

        # 3. Pro-rata based on days vs 30 days
        days = (end_date - start_date).days + 1
        base_monthly = self.get_target_for_month(start_date.year, start_date.month)
        if days == 7:  # A week
            return round(base_monthly / 4.0, 2)
        elif days == 1:  # A single day
            return round(base_monthly / 26.0, 2)
        else:
            return round(base_monthly * (days / 30.0), 2)

    def get_sales_achieved(self, month=None, year=None, start_date=None, end_date=None):
        """Calculates total sales achieved from 'Won' quotations in period, accounting for assisted splits."""
        query = Quotation.select().where(
            ((Quotation.sales_person == self) | (Quotation.assisted_by == self)) &
            (Quotation.status == Quotation.STATUS_WON)
        )
        if start_date and end_date:
            query = query.where(
                (Quotation.quotation_date >= start_date) &
                (Quotation.quotation_date <= end_date)
            )
        elif year and month:
            query = query.where(
                (Quotation.quotation_date.year == year) &
                (Quotation.quotation_date.month == month)
            )
        total = 0.0
        for q in query:
            total += q.get_credit_for_salesperson(self.id)
        return round(float(total), 2)

    def get_pipeline_value(self, month=None, year=None, start_date=None, end_date=None):
        """Calculates total sales pipeline from 'Open' & 'In-Review' quotations, accounting for assisted splits."""
        query = Quotation.select().where(
            ((Quotation.sales_person == self) | (Quotation.assisted_by == self)) &
            (Quotation.status.in_([Quotation.STATUS_OPEN, Quotation.STATUS_IN_REVIEW]))
        )
        if start_date and end_date:
            query = query.where(
                (Quotation.quotation_date >= start_date) &
                (Quotation.quotation_date <= end_date)
            )
        elif year and month:
            query = query.where(
                (Quotation.quotation_date.year == year) &
                (Quotation.quotation_date.month == month)
            )
        total = 0.0
        for q in query:
            total += q.get_credit_for_salesperson(self.id)
        return round(float(total), 2)

    def get_balance_to_target(self, month=None, year=None, start_date=None, end_date=None, target_amount=None):
        achieved = self.get_sales_achieved(month=month, year=year, start_date=start_date, end_date=end_date)
        if target_amount is None:
            if start_date and end_date:
                target_amount = self.get_target_for_period(start_date, end_date)
            elif year and month:
                target_amount = self.get_target_for_month(year, month)
            else:
                target_amount = self.monthly_target
        return max(0.0, round(target_amount - achieved, 2))

    def get_target_percentage(self, month=None, year=None, start_date=None, end_date=None, target_amount=None):
        if target_amount is None:
            if start_date and end_date:
                target_amount = self.get_target_for_period(start_date, end_date)
            elif year and month:
                target_amount = self.get_target_for_month(year, month)
            else:
                target_amount = self.monthly_target
        if target_amount <= 0:
            return 100.0
        achieved = self.get_sales_achieved(month=month, year=year, start_date=start_date, end_date=end_date)
        return round((achieved / target_amount) * 100.0, 1)


class Customer(BaseModel):
    """Customer information and profile."""
    name = CharField(max_length=150)
    mobile_number = CharField(max_length=30)
    email = CharField(max_length=120, null=True)
    delivery_address = TextField()
    site_location = CharField(max_length=150, null=True)
    notes = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "customers"

    def get_quote_count(self):
        if hasattr(self, '_cached_quote_count') and self._cached_quote_count is not None:
            return self._cached_quote_count
        val = Quotation.select().where(Quotation.customer == self).count()
        self._cached_quote_count = val
        return val

    def get_total_won_value(self):
        if hasattr(self, '_cached_total_won') and self._cached_total_won is not None:
            return self._cached_total_won
        val = Quotation.select(fn.SUM(Quotation.net_total)).where(
            (Quotation.customer == self) &
            (Quotation.status == Quotation.STATUS_WON)
        ).scalar()
        val = float(val or 0.0)
        self._cached_total_won = val
        return val


class Quotation(BaseModel):
    """Ceramic & Tile Quotation."""
    STATUS_OPEN = "Open"
    STATUS_WON = "Won"
    STATUS_LOST = "Lost"
    STATUS_IN_REVIEW = "In-Review"

    ALL_STATUSES = [STATUS_OPEN, STATUS_IN_REVIEW, STATUS_WON, STATUS_LOST]

    quotation_number = CharField(max_length=60, unique=True, index=True)
    quotation_date = DateField(default=date.today, index=True)
    
    # Relationships
    customer = ForeignKeyField(Customer, backref="quotations", on_delete="CASCADE")
    sales_person = ForeignKeyField(SalesPerson, backref="quotations", on_delete="CASCADE")
    
    # Snapshot fields for audit and quick rendering
    customer_name = CharField(max_length=150)
    customer_phone = CharField(max_length=30)
    delivery_address = TextField()
    sales_person_name = CharField(max_length=120)

    # Status & Approvals
    status = CharField(max_length=30, default=STATUS_OPEN, index=True)
    manager_approval_note = TextField(null=True)
    approved_by = ForeignKeyField(SalesPerson, null=True, backref="approved_quotations")
    approved_at = DateTimeField(null=True)

    # Financial Totals & Tax Breakdown
    tax_mode = CharField(max_length=20, default="exclusive")  # 'exclusive' or 'inclusive'
    taxable_amount = FloatField(default=0.0)
    cgst_amount = FloatField(default=0.0)
    sgst_amount = FloatField(default=0.0)
    total_tax = FloatField(default=0.0)
    gross_total = FloatField(default=0.0)
    round_off = FloatField(default=0.0)  # Can be positive or negative discount/roundoff
    net_total = FloatField(default=0.0)
    
    # Additional Details
    project_name = CharField(max_length=150, null=True)
    special_notes = TextField(null=True)

    # Assisted Salesperson & Sales Split Collaboration
    assisted_by = ForeignKeyField(SalesPerson, null=True, backref="assisted_quotations", on_delete="SET NULL")
    assisted_by_name = CharField(max_length=120, null=True)
    split_type = CharField(max_length=20, default="none")  # 'none', 'percentage', 'amount'
    assisted_share_value = FloatField(default=0.0)
    primary_share_amount = FloatField(default=0.0)
    assisted_share_amount = FloatField(default=0.0)
    
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "quotations"

    def get_credit_for_salesperson(self, sales_person_id: int) -> float:
        """Returns the net sales amount credited to the given salesperson on this quote."""
        try:
            sp_id = int(sales_person_id)
        except (ValueError, TypeError):
            return 0.0

        asst_id = getattr(self, "assisted_by_id", None)
        split_type = getattr(self, "split_type", "none") or "none"

        if asst_id and split_type in ("percentage", "amount"):
            if int(self.sales_person_id) == sp_id:
                prim = getattr(self, "primary_share_amount", 0.0) or 0.0
                if prim > 0:
                    return float(prim)
                asst_amt = getattr(self, "assisted_share_amount", 0.0) or 0.0
                return max(0.0, round(float(self.net_total) - float(asst_amt), 2))
            elif int(asst_id) == sp_id:
                asst = getattr(self, "assisted_share_amount", 0.0) or 0.0
                if asst > 0:
                    return float(asst)
                val = getattr(self, "assisted_share_value", 0.0) or 0.0
                if split_type == "percentage":
                    return round(float(self.net_total) * (float(val) / 100.0), 2)
                else:
                    return round(float(val), 2)
        else:
            if int(self.sales_person_id) == sp_id:
                return float(self.net_total)
        return 0.0

    def calculate_totals(self):
        """Recalculates taxable, tax, gross and net totals from child items."""
        taxable_sum = 0.0
        gst_sum = 0.0
        gross_sum = 0.0
        for area in self.areas:
            for item in area.items:
                tot = float(item.total_amount or 0.0)
                t_mode = getattr(item, "tax_mode", "exclusive") or "exclusive"
                t_pct = float(getattr(item, "tax_percent", 18.0) or 18.0)
                if t_mode == "inclusive":
                    line_gross = tot
                    t_amt = round(line_gross / (1.0 + t_pct / 100.0), 2)
                    g_amt = round(line_gross - t_amt, 2)
                else:
                    t_amt = tot
                    g_amt = round(t_amt * (t_pct / 100.0), 2)
                    line_gross = round(t_amt + g_amt, 2)
                taxable_sum += t_amt
                gst_sum += g_amt
                gross_sum += line_gross

        self.taxable_amount = round(taxable_sum, 2)
        self.cgst_amount = round(gst_sum / 2.0, 2)
        self.sgst_amount = round(gst_sum - self.cgst_amount, 2)
        self.total_tax = round(gst_sum, 2)
        self.gross_total = round(gross_sum, 2)
        self.net_total = round(self.gross_total + self.round_off, 2)
        return self.gross_total, self.net_total

    def get_cleared_payments(self):
        if hasattr(self, '_cached_cleared_payments') and self._cached_cleared_payments is not None:
            return self._cached_cleared_payments
        val = Payment.select(fn.SUM(Payment.amount)).where(
            (Payment.quotation == self) &
            (Payment.status == Payment.STATUS_CLEARED)
        ).scalar()
        val = float(val or 0.0)
        self._cached_cleared_payments = val
        return val

    def get_pending_payments(self):
        if hasattr(self, '_cached_pending_payments') and self._cached_pending_payments is not None:
            return self._cached_pending_payments
        val = Payment.select(fn.SUM(Payment.amount)).where(
            (Payment.quotation == self) &
            (Payment.status == Payment.STATUS_PENDING)
        ).scalar()
        val = float(val or 0.0)
        self._cached_pending_payments = val
        return val

    def get_outstanding_balance(self):
        cleared = self.get_cleared_payments()
        return max(0.0, round(self.net_total - cleared, 2))

    def get_payment_status(self):
        cleared = self.get_cleared_payments()
        if cleared >= self.net_total and self.net_total > 0:
            return "Fully Paid"
        elif cleared > 0:
            return "Partially Paid"
        return "Unpaid"


class QuotationArea(BaseModel):
    """Section/Area grouping within a quotation (e.g. Kids Bathroom, Ground Floor)."""
    quotation = ForeignKeyField(Quotation, backref="areas", on_delete="CASCADE")
    area_name = CharField(max_length=120)
    display_order = IntegerField(default=1)

    class Meta:
        table_name = "quotation_areas"
        indexes = (
            (('quotation', 'display_order'), False),
        )


class QuotationItem(BaseModel):
    """Individual line item within an area section."""
    TYPE_BOX = "Box"
    TYPE_PIECES = "Pieces"
    TYPE_SQFT = "Sqft"
    TYPE_BAGS = "Bags"
    TYPE_NOS = "Nos"
    ALL_PRODUCT_TYPES = [TYPE_BOX, TYPE_PIECES, TYPE_SQFT, TYPE_BAGS, TYPE_NOS]

    area = ForeignKeyField(QuotationArea, backref="items", on_delete="CASCADE")
    quotation = ForeignKeyField(Quotation, backref="items", on_delete="CASCADE")
    sl_no = IntegerField(default=1)
    description = CharField(max_length=255)
    size = CharField(max_length=60)  # e.g., "1200X1800", "600X600"
    brand = CharField(max_length=120, default="")  # e.g., "Kajaria", "Simpolo"
    product_type = CharField(max_length=30, default="Box")  # 'Box', 'Pieces', 'Sqft', 'Bags', 'Nos'
    coverage_area = FloatField(default=0.0)  # Sqft coverage per box
    quantity_sqft = FloatField(default=0.0)
    rate_per_sqft = FloatField(default=0.0)
    quantity_boxes = FloatField(default=0.0)
    rate_per_box = FloatField(default=0.0)
    tax_mode = CharField(max_length=20, default="exclusive")  # 'exclusive' or 'inclusive'
    tax_percent = FloatField(default=18.0)
    taxable_amount = FloatField(default=0.0)
    gst_amount = FloatField(default=0.0)
    total_amount = FloatField(default=0.0)

    class Meta:
        table_name = "quotation_items"


class TileBrand(BaseModel):
    """Tile manufacturer or brand master catalog."""
    name = CharField(max_length=150, unique=True)
    description = CharField(max_length=255, null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "tile_brands"


class BrandSizeCoverage(BaseModel):
    """Tile size and box coverage area specification for a brand."""
    TYPE_BOX = "Box"
    TYPE_PIECES = "Pieces"
    TYPE_SQFT = "Sqft"
    TYPE_BAGS = "Bags"
    TYPE_NOS = "Nos"
    ALL_PRODUCT_TYPES = [TYPE_BOX, TYPE_PIECES, TYPE_SQFT, TYPE_BAGS, TYPE_NOS]

    brand = ForeignKeyField(TileBrand, backref="size_coverages", on_delete="CASCADE")
    size = CharField(max_length=80)  # e.g., "1200X1800"
    product_type = CharField(max_length=30, default="Box")  # 'Box', 'Pieces', 'Sqft', 'Bags', 'Nos'
    coverage_sqft = FloatField(default=15.5)  # Coverage Area in Sqft per box
    pieces_per_box = IntegerField(default=2)
    default_rate_sqft = FloatField(default=0.0)
    default_rate_box = FloatField(default=0.0)

    class Meta:
        table_name = "brand_size_coverages"


class Payment(BaseModel):
    """Payment records against a quotation."""
    STATUS_PENDING = "Pending"
    STATUS_CLEARED = "Cleared"

    MODE_GPAY = "GPay"
    MODE_PHONEPE = "PhonePe"
    MODE_BANK = "Bank Transfer (NEFT/RTGS/IMPS)"
    MODE_CHEQUE = "Cheque"
    MODE_CASH = "Cash"

    ALL_MODES = [MODE_GPAY, MODE_PHONEPE, MODE_BANK, MODE_CHEQUE, MODE_CASH]
    ALL_STATUSES = [STATUS_PENDING, STATUS_CLEARED]

    quotation = ForeignKeyField(Quotation, backref="payments", on_delete="CASCADE")
    amount = FloatField()
    payment_mode = CharField(max_length=50, default=MODE_GPAY)
    payment_date = DateField(default=date.today, index=True)
    status = CharField(max_length=30, default=STATUS_CLEARED, index=True)
    reference_number = CharField(max_length=100, null=True)
    notes = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "payments"


class SalesTarget(BaseModel):
    """Specific targets allocated to a salesperson for monthly, weekly, or custom date periods."""
    TARGET_MONTHLY = "Monthly"
    TARGET_WEEKLY = "Weekly"
    TARGET_CUSTOM = "Custom"
    TARGET_TYPES = [TARGET_MONTHLY, TARGET_WEEKLY, TARGET_CUSTOM]

    sales_person = ForeignKeyField(SalesPerson, backref="assigned_targets", on_delete="CASCADE")
    target_type = CharField(max_length=30, default=TARGET_MONTHLY)  # Monthly, Weekly, Custom

    # Date Scope
    start_date = DateField()
    end_date = DateField()

    # Period Identifiers
    year = IntegerField(null=True)        # e.g., 2026
    month = IntegerField(null=True)       # 1 - 12 (if Monthly)
    week_number = IntegerField(null=True) # 1 - 53 (if Weekly)
    period_label = CharField(max_length=150) # e.g. "October 2026", "Week 42 (12 Oct - 18 Oct)", "Diwali Promotion"

    target_amount = FloatField(default=500000.0)
    notes = TextField(null=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "sales_targets"

    @classmethod
    def set_monthly_target(cls, sales_person, year: int, month: int, amount: float, notes: str = None):
        """Sets or alters a target specifically for a single month."""
        start_date = date(year, month, 1)
        if month == 12:
            next_m = date(year + 1, 1, 1)
        else:
            next_m = date(year, month + 1, 1)
        end_date = next_m - timedelta(days=1)
        period_label = start_date.strftime("%B %Y")

        record, created = cls.get_or_create(
            sales_person=sales_person,
            target_type=cls.TARGET_MONTHLY,
            year=year,
            month=month,
            defaults={
                "start_date": start_date,
                "end_date": end_date,
                "period_label": period_label,
                "target_amount": float(amount),
                "notes": notes,
            }
        )
        if not created:
            record.target_amount = float(amount)
            record.start_date = start_date
            record.end_date = end_date
            record.period_label = period_label
            if notes is not None:
                record.notes = notes
            record.updated_at = datetime.now()
            record.save()
        return record

    @classmethod
    def set_weekly_target(cls, sales_person, start_date: date, amount: float, notes: str = None):
        """Sets or alters a target for a specific week (Monday to Sunday)."""
        mon = start_date - timedelta(days=start_date.weekday())
        sun = mon + timedelta(days=6)
        week_num = mon.isocalendar()[1]
        period_label = f"Week {week_num} ({mon.strftime('%d %b')} - {sun.strftime('%d %b %Y')})"

        record, created = cls.get_or_create(
            sales_person=sales_person,
            target_type=cls.TARGET_WEEKLY,
            start_date=mon,
            end_date=sun,
            defaults={
                "year": mon.year,
                "month": mon.month,
                "week_number": week_num,
                "period_label": period_label,
                "target_amount": float(amount),
                "notes": notes,
            }
        )
        if not created:
            record.target_amount = float(amount)
            record.week_number = week_num
            record.period_label = period_label
            if notes is not None:
                record.notes = notes
            record.updated_at = datetime.now()
            record.save()
        return record

    @classmethod
    def set_custom_target(cls, sales_person, start_date: date, end_date: date, amount: float, label: str = None, notes: str = None):
        """Sets or alters a target for a custom date range."""
        if not label:
            label = f"Custom ({start_date.strftime('%d %b')} - {end_date.strftime('%d %b %Y')})"

        record, created = cls.get_or_create(
            sales_person=sales_person,
            target_type=cls.TARGET_CUSTOM,
            start_date=start_date,
            end_date=end_date,
            defaults={
                "year": start_date.year,
                "month": start_date.month,
                "period_label": label,
                "target_amount": float(amount),
                "notes": notes,
            }
        )
        if not created:
            record.target_amount = float(amount)
            record.period_label = label
            if notes is not None:
                record.notes = notes
            record.updated_at = datetime.now()
            record.save()
        return record


class CompanySetting(BaseModel):
    """Persistent customizable company branding, address, bank details, and T&C."""
    company_name = CharField(max_length=200, default="AMA CERAMICS PVT LTD")
    tagline = CharField(max_length=255, default="Architectural Surfaces, Vitrified Tiles & Luxury Sanitaries")
    logo_path = CharField(max_length=500, null=True)
    address_line1 = CharField(max_length=255, default="Showroom & Experience Center: Plot 48, Ceramic Industrial Corridor")
    address_line2 = CharField(max_length=255, default="S.G. Highway, Ahmedabad - 380054, Gujarat, India")
    phone = CharField(max_length=150, default="+91 98250 12345 / +91 79 2654 8900")
    email = CharField(max_length=150, default="sales@amaceramics.com | info@amaceramics.com")
    website = CharField(max_length=150, default="www.amaceramics.com")
    gstin = CharField(max_length=50, default="24AAACA5678Q1Z4")
    state = CharField(max_length=100, default="Gujarat (Code: 24)")

    # Bank Details
    bank_name = CharField(max_length=150, default="HDFC Bank Ltd")
    account_name = CharField(max_length=200, default="AMA CERAMICS PRIVATE LIMITED")
    account_number = CharField(max_length=60, default="50200088991234")
    ifsc_code = CharField(max_length=50, default="HDFC0001245")
    branch = CharField(max_length=200, default="Bodakdev - S.G. Highway Branch, Ahmedabad")
    account_type = CharField(max_length=50, default="Current Account")
    upi_details = TextField(default="GPay / PhonePe / Paytm / UPI Accepted at Showroom Counter.\nCheques in favor of: 'AMA CERAMICS PRIVATE LIMITED'")

    # Signatures
    store_manager_title = CharField(max_length=100, default="Store Manager")
    store_manager_name = CharField(max_length=120, default="Rajesh Sharma")
    store_manager_phone = CharField(max_length=50, default="+91 98250 12345")
    sales_associate_title = CharField(max_length=100, default="Showroom Sales Associate")

    # Standard Terms (JSON array)
    terms_json = TextField(null=True)
    updated_at = DateTimeField(default=datetime.now)

    _cached_instance = None

    class Meta:
        table_name = "company_settings"

    @classmethod
    def invalidate_cache(cls):
        cls._cached_instance = None

    def save(self, *args, **kwargs):
        CompanySetting.invalidate_cache()
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Fetches the singleton company setting row, caching in memory for instant reuse."""
        if cls._cached_instance is not None:
            return cls._cached_instance

        import json
        setting = cls.select().first()
        if not setting:
            from app.config import (
                BASE_DIR,
                COMPANY_CONFIG,
                BANK_DETAILS,
                SIGNATORIES,
                STANDARD_TERMS_AND_CONDITIONS,
            )
            def_logo = BASE_DIR / "assets" / "default_logo.png"
            logo_p = str(def_logo) if def_logo.exists() else None
            setting = cls.create(
                company_name=COMPANY_CONFIG["name"],
                tagline=COMPANY_CONFIG["tagline"],
                logo_path=logo_p,
                address_line1=COMPANY_CONFIG["address_line1"],
                address_line2=COMPANY_CONFIG["address_line2"],
                phone=COMPANY_CONFIG["phone"],
                email=COMPANY_CONFIG["email"],
                website=COMPANY_CONFIG["website"],
                gstin=COMPANY_CONFIG["gstin"],
                state=COMPANY_CONFIG["state"],
                bank_name=BANK_DETAILS["bank_name"],
                account_name=BANK_DETAILS["account_name"],
                account_number=BANK_DETAILS["account_number"],
                ifsc_code=BANK_DETAILS["ifsc_code"],
                branch=BANK_DETAILS["branch"],
                account_type=BANK_DETAILS.get("account_type", "Current Account"),
                store_manager_title=SIGNATORIES["store_manager_title"],
                store_manager_name=SIGNATORIES["store_manager_name"],
                store_manager_phone=SIGNATORIES["store_manager_phone"],
                sales_associate_title=SIGNATORIES["sales_associate_title"],
                terms_json=json.dumps(STANDARD_TERMS_AND_CONDITIONS),
            )
        elif not setting.logo_path:
            from app.config import BASE_DIR
            def_logo = BASE_DIR / "assets" / "default_logo.png"
            if def_logo.exists():
                setting.logo_path = str(def_logo)
                setting.save()
        cls._cached_instance = setting
        return setting

    def get_terms_list(self):
        import json
        if self.terms_json:
            try:
                return json.loads(self.terms_json)
            except Exception:
                pass
        from app.config import STANDARD_TERMS_AND_CONDITIONS
        return list(STANDARD_TERMS_AND_CONDITIONS)

    def set_terms_list(self, terms_list):
        import json
        self.terms_json = json.dumps(terms_list)
        self.save()


def init_database():
    """Initializes tables and creates schema automatically with high-performance indexes."""
    db.connect(reuse_if_open=True)
    db.create_tables([
        SalesPerson,
        Customer,
        Quotation,
        QuotationArea,
        QuotationItem,
        Payment,
        SalesTarget,
        CompanySetting,
        TileBrand,
        BrandSizeCoverage
    ])
    # Safe column migration for quotation_items
    try:
        cursor = db.execute_sql("PRAGMA table_info(quotation_items)")
        cols = [row[1] for row in cursor.fetchall()]
        if "brand" not in cols:
            db.execute_sql("ALTER TABLE quotation_items ADD COLUMN brand VARCHAR(120) DEFAULT ''")
        if "coverage_area" not in cols:
            db.execute_sql("ALTER TABLE quotation_items ADD COLUMN coverage_area REAL DEFAULT 0.0")
        if "tax_mode" not in cols:
            db.execute_sql("ALTER TABLE quotation_items ADD COLUMN tax_mode VARCHAR(20) DEFAULT 'exclusive'")
        if "tax_percent" not in cols:
            db.execute_sql("ALTER TABLE quotation_items ADD COLUMN tax_percent REAL DEFAULT 18.0")
        if "taxable_amount" not in cols:
            db.execute_sql("ALTER TABLE quotation_items ADD COLUMN taxable_amount REAL DEFAULT 0.0")
        if "product_type" not in cols:
            db.execute_sql("ALTER TABLE quotation_items ADD COLUMN product_type VARCHAR(30) DEFAULT 'Box'")
    except Exception:
        pass

    # Safe column migration for brand_size_coverages
    try:
        cursor_b = db.execute_sql("PRAGMA table_info(brand_size_coverages)")
        cols_b = [row[1] for row in cursor_b.fetchall()]
        if "product_type" not in cols_b:
            db.execute_sql("ALTER TABLE brand_size_coverages ADD COLUMN product_type VARCHAR(30) DEFAULT 'Box'")
    except Exception:
        pass

    # Safe column migration for quotations
    try:
        cursor_q = db.execute_sql("PRAGMA table_info(quotations)")
        cols_q = [row[1] for row in cursor_q.fetchall()]
        if "tax_mode" not in cols_q:
            db.execute_sql("ALTER TABLE quotations ADD COLUMN tax_mode VARCHAR(20) DEFAULT 'exclusive'")
        if "taxable_amount" not in cols_q:
            db.execute_sql("ALTER TABLE quotations ADD COLUMN taxable_amount REAL DEFAULT 0.0")
        if "cgst_amount" not in cols_q:
            db.execute_sql("ALTER TABLE quotations ADD COLUMN cgst_amount REAL DEFAULT 0.0")
        if "sgst_amount" not in cols_q:
            db.execute_sql("ALTER TABLE quotations ADD COLUMN sgst_amount REAL DEFAULT 0.0")
        if "total_tax" not in cols_q:
            db.execute_sql("ALTER TABLE quotations ADD COLUMN total_tax REAL DEFAULT 0.0")
        if "assisted_by_id" not in cols_q:
            db.execute_sql("ALTER TABLE quotations ADD COLUMN assisted_by_id INTEGER NULL")
        if "assisted_by_name" not in cols_q:
            db.execute_sql("ALTER TABLE quotations ADD COLUMN assisted_by_name VARCHAR(120) NULL")
        if "split_type" not in cols_q:
            db.execute_sql("ALTER TABLE quotations ADD COLUMN split_type VARCHAR(20) DEFAULT 'none'")
        if "assisted_share_value" not in cols_q:
            db.execute_sql("ALTER TABLE quotations ADD COLUMN assisted_share_value REAL DEFAULT 0.0")
        if "primary_share_amount" not in cols_q:
            db.execute_sql("ALTER TABLE quotations ADD COLUMN primary_share_amount REAL DEFAULT 0.0")
        if "assisted_share_amount" not in cols_q:
            db.execute_sql("ALTER TABLE quotations ADD COLUMN assisted_share_amount REAL DEFAULT 0.0")
    except Exception:
        pass

    # High-performance composite indexes for instant report generation & table filters
    try:
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_quote_status_date ON quotations(status, quotation_date)")
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_quote_sp_status_date ON quotations(sales_person_id, status, quotation_date)")
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_quote_assisted_status ON quotations(assisted_by_id, status, quotation_date)")
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_quote_cust_status ON quotations(customer_id, status)")
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_payment_quote_status ON payments(quotation_id, status)")
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_payment_status_date ON payments(status, payment_date)")
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_sales_target_sp_type ON sales_targets(sales_person_id, target_type, year, month)")
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_sales_target_period ON sales_targets(sales_person_id, start_date, end_date)")
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_brand_size ON brand_size_coverages(brand_id, size)")
    except Exception:
        pass

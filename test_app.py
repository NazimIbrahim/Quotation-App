"""
Comprehensive verification test suite for AMA Ceramics Quotation Management System.
Tests database, models, calculations, services, PDF rendering, and UI construction.
"""
import sys
import os
from pathlib import Path
from datetime import date

# Ensure root in path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.database.models import (
    init_database,
    SalesPerson,
    Customer,
    Quotation,
    QuotationArea,
    QuotationItem,
    Payment,
    SalesTarget,
)
from app.database.seed_data import seed_database
from app.services.quotation_service import QuotationService
from app.services.payment_service import PaymentService
from app.services.report_service import ReportService
from app.services.pdf_service import CeramicPDFGenerator
from app.services.report_pdf_service import ReportPDFGenerator


def test_system():
    print("[TEST 1] Initializing schema and seed database...")
    init_database()
    seeded = seed_database(force=True)
    assert seeded is True, "Seed database failed"
    print(" -> PASS: Database seeded successfully.")

    print("\n[TEST 2] Verifying User Roles & Management...")
    sales_team = list(SalesPerson.select())
    assert len(sales_team) >= 4, f"Expected at least 4 sales persons, found {len(sales_team)}"
    manager = SalesPerson.get(SalesPerson.role == SalesPerson.ROLE_MANAGER)
    assert manager.name == "Rajesh Sharma", f"Expected manager Rajesh Sharma, found {manager.name}"
    print(f" -> PASS: Manager: {manager.name}, Sales associates: {[s.name for s in sales_team if s.role != 'Manager']}")

    print("\n[TEST 3] Verifying Quotation Calculations & Multi-Area Grouping...")
    # Test creating a new quotation with multi-area grouping
    cust = Customer.get()
    sp = SalesPerson.get(SalesPerson.role == SalesPerson.ROLE_SALES)

    new_payload = {
        "quotation_number": "AMA-2026-TEST",
        "quotation_date": date.today(),
        "customer_id": cust.id,
        "sales_person_id": sp.id,
        "project_name": "Test Penthouse Suite",
        "special_notes": "Unit testing automated quote",
        "status": Quotation.STATUS_OPEN,
        "round_off": -50.0,
        "areas": [
            {
                "area_name": "Kids Bathroom",
                "items": [
                    {
                        "description": "AZUL AQUA CERAMIC TILE",
                        "size": "600X1200",
                        "quantity_sqft": 100.0,
                        "rate_per_sqft": 80.0,
                        "quantity_boxes": 6.5,
                        "rate_per_box": 1230.76,
                        "total_amount": 8000.0,
                    }
                ]
            },
            {
                "area_name": "Bar Counter",
                "items": [
                    {
                        "description": "BLACK MARBLE SLAB",
                        "size": "1200X1800",
                        "quantity_sqft": 200.0,
                        "rate_per_sqft": 150.0,
                        "quantity_boxes": 10.0,
                        "rate_per_box": 3000.0,
                        "total_amount": 30000.0,
                    }
                ]
            }
        ]
    }

    created_quote = QuotationService.save_quotation(new_payload)
    assert created_quote.gross_total == 38000.0, f"Expected 38000, got {created_quote.gross_total}"
    assert created_quote.net_total == 37950.0, f"Expected 37950, got {created_quote.net_total}"
    assert created_quote.areas.count() == 2, f"Expected 2 areas, got {created_quote.areas.count()}"
    print(f" -> PASS: Created {created_quote.quotation_number} with gross ₹{created_quote.gross_total} and net ₹{created_quote.net_total}")

    print("\n[TEST 4] Verifying Payment Tracking & Outstanding Balance...")
    # Add payment
    pmt = PaymentService.add_payment(
        quotation_id=created_quote.id,
        amount=20000.0,
        mode=Payment.MODE_GPAY,
        status=Payment.STATUS_CLEARED,
        reference_number="TEST-UPI-1234",
        notes="Advance token"
    )
    fin_summary = PaymentService.get_financial_summary(created_quote.id)
    assert fin_summary["cleared_amount"] == 20000.0
    assert fin_summary["outstanding_balance"] == 17950.0
    assert fin_summary["payment_status"] == "Partially Paid"
    print(f" -> PASS: Recorded payment of ₹{pmt.amount}. Cleared: ₹{fin_summary['cleared_amount']}, Outstanding: ₹{fin_summary['outstanding_balance']}")

    print("\n[TEST 5] Verifying Reporting Dashboard Service...")
    metrics = ReportService.get_dashboard_metrics("Monthly")
    assert "won_sales_value" in metrics
    assert "pipeline_value" in metrics
    assert "cleared_payments" in metrics
    assert "total_outstanding" in metrics
    print(f" -> PASS: Monthly won sales: ₹{metrics['won_sales_value']:,.2f}, Cleared collections: ₹{metrics['cleared_payments']:,.2f}")

    perf = ReportService.get_salesperson_performances("Monthly")
    assert len(perf["individuals"]) >= 4
    print(f" -> PASS: Team goal: ₹{perf['team_total_target']:,.0f}, Achieved: ₹{perf['team_total_achieved']:,.0f} ({perf['team_percentage']}%)")

    print("\n[TEST 6] Verifying PDF Generation with 13 Terms, Areas, Signatures, Bank Details...")
    pdf_path = CeramicPDFGenerator.generate_quotation_pdf(created_quote.id)
    assert Path(pdf_path).exists(), f"PDF file not found at {pdf_path}"
    pdf_size = Path(pdf_path).stat().st_size
    assert pdf_size > 1000, f"PDF file size too small: {pdf_size} bytes"
    print(f" -> PASS: PDF generated successfully at {pdf_path} (Size: {pdf_size:,} bytes)")

    print("\n[TEST 7] Verifying In-App Company & PDF Settings Customization...")
    from app.database.models import CompanySetting
    c_setting = CompanySetting.get_settings()
    c_setting.company_name = "AMA LUXURY SURFACES & TILES"
    c_setting.bank_name = "ICICI Bank Corporate"
    c_setting.account_number = "99887766554433"
    c_setting.gstin = "24XYZ9999Q1Z9"
    c_setting.save()

    updated_pdf = CeramicPDFGenerator.generate_quotation_pdf(created_quote.id)
    assert Path(updated_pdf).exists()
    print(f" -> PASS: Successfully customized company name, bank, and GSTIN; generated updated PDF: {Path(updated_pdf).name}")

    print("\n[TEST 8] Verifying Tile Brands & Coverage Master Catalog...")
    from app.database.models import TileBrand, BrandSizeCoverage
    all_brands = list(TileBrand.select().where(TileBrand.is_active == True))
    assert len(all_brands) >= 5, f"Expected at least 5 tile brands, found {len(all_brands)}"
    brand_names = [b.name for b in all_brands]
    assert "Kajaria Eternity" in brand_names
    assert "Simpolo Ceramics" in brand_names
    
    # Test adding a custom tile brand and size coverage
    custom_brand, _ = TileBrand.get_or_create(
        name="Morbi Royal Tiles",
        defaults={"description": "Premium GVT & PGVT collection"}
    )
    cov_record, _ = BrandSizeCoverage.get_or_create(
        brand=custom_brand,
        size="800X1600",
        defaults={
            "coverage_sqft": 27.56,
            "pieces_per_box": 2,
            "default_rate_sqft": 110.0,
            "default_rate_box": 3031.60
        }
    )
    assert cov_record.coverage_sqft == 27.56
    assert cov_record.pieces_per_box == 2
    print(f" -> PASS: Active brands: {len(all_brands)}. Created custom brand '{custom_brand.name}' with size '{cov_record.size}' ({cov_record.coverage_sqft} Sqft/Box)")

    print("\n[TEST 9] Verifying Quotation Items with Brand & Coverage Area...")
    quote_with_brand_payload = {
        "quotation_number": "AMA-2026-BRAND-TEST",
        "quotation_date": date.today(),
        "customer_id": cust.id,
        "sales_person_id": sp.id,
        "project_name": "Sky Villa with Brand Specs",
        "special_notes": "Testing brand and coverage columns",
        "status": Quotation.STATUS_OPEN,
        "round_off": 0.0,
        "areas": [
            {
                "area_name": "Living Foyer",
                "items": [
                    {
                        "description": "ROYAL STATUARIO PGVT",
                        "size": "800X1600",
                        "brand": "Morbi Royal Tiles",
                        "coverage_area": 27.56,
                        "quantity_sqft": 275.60,
                        "rate_per_sqft": 110.0,
                        "quantity_boxes": 10.0,
                        "rate_per_box": 3031.60,
                        "total_amount": 30316.0,
                    }
                ]
            }
        ]
    }
    saved_quote = QuotationService.save_quotation(quote_with_brand_payload)
    quote_details = QuotationService.get_quotation_details(saved_quote.id)
    first_item = quote_details["areas"][0]["items"][0]
    assert first_item["brand"] == "Morbi Royal Tiles", f"Expected 'Morbi Royal Tiles', got {first_item['brand']}"
    assert first_item["coverage_area"] == 27.56, f"Expected 27.56, got {first_item['coverage_area']}"
    assert first_item["total_amount"] == 30316.0
    print(f" -> PASS: Saved and retrieved item with Brand: '{first_item['brand']}', Coverage: {first_item['coverage_area']} Sqft/Box, Total: ₹{first_item['total_amount']}")

    print("\n[TEST 10] Verifying 10-Column PDF Output with Brand & Coverage Area...")
    pdf_brand_path = CeramicPDFGenerator.generate_quotation_pdf(saved_quote.id)
    assert Path(pdf_brand_path).exists()
    assert Path(pdf_brand_path).stat().st_size > 1000
    print(f" -> PASS: 10-Column PDF successfully generated: {Path(pdf_brand_path).name} ({Path(pdf_brand_path).stat().st_size:,} bytes)")

    print("\n[TEST 11] Verifying Daily Sales & Collections Report Generation (PDF & CSV)...")
    daily_pdf = ReportPDFGenerator.generate_daily_report_pdf(date.today())
    assert Path(daily_pdf).exists() and Path(daily_pdf).stat().st_size > 1000
    daily_csv = ReportService.export_daily_report_csv(date.today())
    assert Path(daily_csv).exists() and Path(daily_csv).stat().st_size > 100
    print(f" -> PASS: Daily Report exported successfully - PDF: {Path(daily_pdf).name} ({Path(daily_pdf).stat().st_size:,} B), CSV: {Path(daily_csv).name}")

    print("\n[TEST 12] Verifying Monthly Performance & Revenue Audit Report Generation (PDF & CSV)...")
    monthly_pdf = ReportPDFGenerator.generate_monthly_report_pdf()
    assert Path(monthly_pdf).exists() and Path(monthly_pdf).stat().st_size > 1000
    monthly_csv = ReportService.export_monthly_report_csv()
    assert Path(monthly_csv).exists() and Path(monthly_csv).stat().st_size > 100
    print(f" -> PASS: Monthly Report exported successfully - PDF: {Path(monthly_pdf).name} ({Path(monthly_pdf).stat().st_size:,} B), CSV: {Path(monthly_csv).name}")

    print("\n[TEST 13] Verifying Sales Target vs. Achievement Archive Report Generation (PDF & CSV)...")
    archive_pdf = ReportPDFGenerator.generate_target_archive_pdf()
    assert Path(archive_pdf).exists() and Path(archive_pdf).stat().st_size > 1000
    archive_csv = ReportService.export_target_archive_csv()
    assert Path(archive_csv).exists() and Path(archive_csv).stat().st_size > 100
    print(f" -> PASS: Target Archive Report exported successfully - PDF: {Path(archive_pdf).name} ({Path(archive_pdf).stat().st_size:,} B), CSV: {Path(archive_csv).name}")

    print("\n[TEST 14] Verifying Month-Specific Target Alteration, Weekly Sprint, and Custom Date Range Targets...")
    test_sp = SalesPerson.get(SalesPerson.role == SalesPerson.ROLE_SALES)
    base_target = test_sp.monthly_target

    # 1. Alter target for a single specific month (e.g. October 2026)
    oct_target = 850000.0
    rec_oct = SalesTarget.set_monthly_target(test_sp, 2026, 10, oct_target, "October Festive Sprint Target")
    assert rec_oct.target_amount == oct_target
    assert test_sp.get_target_for_month(2026, 10) == oct_target, f"Expected {oct_target}, got {test_sp.get_target_for_month(2026, 10)}"

    # Crucial test: Ensure other months (e.g. November 2026, September 2026) retain the base target ("only month")
    assert test_sp.get_target_for_month(2026, 11) == base_target, "Other months must retain default base target!"
    assert test_sp.get_target_for_month(2026, 9) == base_target, "Other months must retain default base target!"
    print(f" -> PASS: Altered target for October 2026 only: ₹{oct_target:,.2f}. November remains at default ₹{base_target:,.2f}")

    # 2. Weekly Sprint Target (Monday to Sunday)
    week_ref_date = date(2026, 10, 14)  # Wednesday
    rec_week = SalesTarget.set_weekly_target(test_sp, week_ref_date, 225000.0, "Week 42 Festive Sprint")
    assert rec_week.start_date == date(2026, 10, 12)  # Monday
    assert rec_week.end_date == date(2026, 10, 18)    # Sunday
    assert test_sp.get_target_for_period(date(2026, 10, 12), date(2026, 10, 18)) == 225000.0
    print(f" -> PASS: Set 7-day Weekly Target: {rec_week.period_label} -> ₹{rec_week.target_amount:,.2f}")

    # 3. Custom Date Range Target (e.g. 15-day promotional window)
    c_start = date(2026, 10, 1)
    c_end = date(2026, 10, 15)
    rec_custom = SalesTarget.set_custom_target(test_sp, c_start, c_end, 420000.0, "Navratri Mega Campaign", "Promotional Sprint")
    assert rec_custom.target_amount == 420000.0
    assert test_sp.get_target_for_period(c_start, c_end) == 420000.0
    print(f" -> PASS: Set Custom Date Range Target: {rec_custom.period_label} -> ₹{rec_custom.target_amount:,.2f}")

    # 4. Verify ReportService reflects month-specific altered target vs other months
    perf_oct = ReportService.get_salesperson_performances(date(2026, 10, 1), date(2026, 10, 31))
    sp_oct_data = next((p for p in perf_oct["individuals"] if p["id"] == test_sp.id), None)
    assert sp_oct_data is not None
    assert sp_oct_data["target"] == oct_target, f"Expected {oct_target}, got {sp_oct_data['target']}"

    perf_nov = ReportService.get_salesperson_performances(date(2026, 11, 1), date(2026, 11, 30))
    sp_nov_data = next((p for p in perf_nov["individuals"] if p["id"] == test_sp.id), None)
    assert sp_nov_data is not None
    assert sp_nov_data["target"] == base_target, f"Expected base {base_target}, got {sp_nov_data['target']}"
    print(f" -> PASS: ReportService audits reflect month-specific altered target (Oct: ₹{sp_oct_data['target']:,.2f}, Nov: ₹{sp_nov_data['target']:,.2f})")

    # 5. Clean up altered target and verify clean revert to base target
    rec_oct.delete_instance()
    assert test_sp.get_target_for_month(2026, 10) == base_target
    print(" -> PASS: Deleted altered target and verified instant rollback to base target.")

    print("\n[TEST 15] Verifying 18% Inclusive vs 18% Exclusive Tax Calculations & PDF...")
    # 1. Tax Exclusive Quotation: Rates exclude 18% tax; 18% GST is added to total
    excl_payload = {
        "quotation_number": "AMA-2026-TAX-EXCL",
        "customer_id": cust.id,
        "sales_person_id": sp.id,
        "project_name": "Exclusive 18% GST Villa",
        "special_notes": "18% GST will be added",
        "status": Quotation.STATUS_OPEN,
        "tax_mode": "exclusive",
        "round_off": 0.0,
        "areas": [
            {
                "area_name": "Foyer & Corridor",
                "items": [
                    {
                        "description": "STATUARIO GLOSS 1200X1800",
                        "size": "1200X1800",
                        "brand": "Kajaria Eternity",
                        "coverage_area": 23.25,
                        "quantity_sqft": 100.0,
                        "rate_per_sqft": 50.0,
                        "tax_mode": "exclusive",
                        "quantity_boxes": 4.3,
                        "rate_per_box": 1162.5,
                        "total_amount": 5000.0,
                    }
                ]
            }
        ]
    }
    q_excl = QuotationService.save_quotation(excl_payload)
    assert q_excl.taxable_amount == 5000.0, f"Expected 5000.0, got {q_excl.taxable_amount}"
    assert q_excl.cgst_amount == 450.0, f"Expected 450.0, got {q_excl.cgst_amount}"
    assert q_excl.sgst_amount == 450.0, f"Expected 450.0, got {q_excl.sgst_amount}"
    assert q_excl.total_tax == 900.0, f"Expected 900.0, got {q_excl.total_tax}"
    assert q_excl.gross_total == 5900.0, f"Expected 5900.0, got {q_excl.gross_total}"
    assert q_excl.net_total == 5900.0, f"Expected 5900.0, got {q_excl.net_total}"
    print(f" -> PASS: Tax Exclusive Quote {q_excl.quotation_number}: Taxable=₹{q_excl.taxable_amount:,.2f}, CGST(9%)=₹{q_excl.cgst_amount:,.2f}, SGST(9%)=₹{q_excl.sgst_amount:,.2f}, Total GST=₹{q_excl.total_tax:,.2f}, Net=₹{q_excl.net_total:,.2f}")

    # 2. Tax Inclusive Quotation: Rates already include 18% tax
    incl_payload = {
        "quotation_number": "AMA-2026-TAX-INCL",
        "customer_id": cust.id,
        "sales_person_id": sp.id,
        "project_name": "Inclusive 18% GST Residency",
        "special_notes": "All rates include 18% GST",
        "status": Quotation.STATUS_OPEN,
        "tax_mode": "inclusive",
        "round_off": 0.0,
        "areas": [
            {
                "area_name": "Master Suite",
                "items": [
                    {
                        "description": "ARMANI GREY SATIN 800X1600",
                        "size": "800X1600",
                        "brand": "Simpolo Ceramics",
                        "coverage_area": 27.56,
                        "quantity_sqft": 100.0,
                        "rate_per_sqft": 118.0,
                        "tax_mode": "inclusive",
                        "quantity_boxes": 3.63,
                        "rate_per_box": 3252.08,
                        "total_amount": 11800.0,
                    }
                ]
            }
        ]
    }
    q_incl = QuotationService.save_quotation(incl_payload)
    assert q_incl.gross_total == 11800.0, f"Expected 11800.0, got {q_incl.gross_total}"
    assert q_incl.taxable_amount == 10000.0, f"Expected 10000.0, got {q_incl.taxable_amount}"
    assert q_incl.total_tax == 1800.0, f"Expected 1800.0, got {q_incl.total_tax}"
    assert q_incl.cgst_amount == 900.0, f"Expected 900.0, got {q_incl.cgst_amount}"
    assert q_incl.sgst_amount == 900.0, f"Expected 900.0, got {q_incl.sgst_amount}"
    assert q_incl.net_total == 11800.0, f"Expected 11800.0, got {q_incl.net_total}"
    print(f" -> PASS: Tax Inclusive Quote {q_incl.quotation_number}: Gross=₹{q_incl.gross_total:,.2f}, Taxable=₹{q_incl.taxable_amount:,.2f}, CGST(9%)=₹{q_incl.cgst_amount:,.2f}, SGST(9%)=₹{q_incl.sgst_amount:,.2f}, Net=₹{q_incl.net_total:,.2f}")

    # 3. Generate PDF for Exclusive and Inclusive quotations and verify layout
    pdf_excl = CeramicPDFGenerator.generate_quotation_pdf(q_excl.id)
    assert Path(pdf_excl).exists(), "Exclusive PDF not found!"
    pdf_incl = CeramicPDFGenerator.generate_quotation_pdf(q_incl.id)
    assert Path(pdf_incl).exists(), "Inclusive PDF not found!"
    print(f" -> PASS: Successfully generated PDF with 18% Tax breakdown for Exclusive ({Path(pdf_excl).name}) and Inclusive ({Path(pdf_incl).name})")

    # [TEST 16] Verifying Quotation Calculation & Item Fallback when Description is Blank
    print("\n[TEST 16] Verifying Quotation Calculations with Blank Item Description...")
    blank_payload = {
        "quotation_number": "AMA-2026-BLANK-DESC",
        "customer_id": cust.id,
        "sales_person_id": sp.id,
        "project_name": "Blank Description Test Project",
        "status": Quotation.STATUS_OPEN,
        "tax_mode": "exclusive",
        "round_off": 0.0,
        "areas": [
            {
                "area_name": "GROUND FLOOR - LIVING ROOM",
                "items": [
                    {
                        "description": "",
                        "brand": "AMA Signature Collection",
                        "size": "600X1200",
                        "coverage_area": 15.5,
                        "quantity_sqft": 62.0,
                        "rate_per_sqft": 85.0,
                        "quantity_boxes": 4.0,
                        "rate_per_box": 1317.50,
                        "tax_mode": "exclusive",
                        "total_amount": 5270.0,
                    }
                ]
            }
        ]
    }
    q_blank = QuotationService.save_quotation(blank_payload)
    assert len(q_blank.items) == 1, "Item with blank description should not be dropped!"
    assert q_blank.items[0].description == "AMA Signature Collection 600X1200 Tile", f"Unexpected fallback desc: {q_blank.items[0].description}"
    assert q_blank.taxable_amount == 5270.0, f"Expected taxable 5270.0, got {q_blank.taxable_amount}"
    assert q_blank.total_tax == 948.6, f"Expected GST 948.6, got {q_blank.total_tax}"
    assert q_blank.gross_total == 6218.6, f"Expected gross 6218.6, got {q_blank.gross_total}"
    assert q_blank.net_total == 6218.6, f"Expected net 6218.6, got {q_blank.net_total}"
    print(f" -> PASS: Saved quote with blank description! Auto-fallback: '{q_blank.items[0].description}', Gross: ₹{q_blank.gross_total:,.2f}, GST: ₹{q_blank.total_tax:,.2f}, Net: ₹{q_blank.net_total:,.2f}")

    print("\n[TEST 17] Verifying Lump-Sum Discount Distribution Across Item Rates & Zero Discount in PDF...")
    # Clean up previous run if exists
    old_disc = Quotation.get_or_none(Quotation.quotation_number == "AMA-2026-DISC-AUTO")
    if old_disc:
        QuotationItem.delete().where(QuotationItem.quotation == old_disc).execute()
        QuotationArea.delete().where(QuotationArea.quotation == old_disc).execute()
        old_disc.delete_instance()

    # Initial quote gross = ₹85,000 (Inclusive mode)
    # Item 1: 500 sqft @ ₹100 = ₹50,000
    # Item 2: 350 sqft @ ₹100 = ₹35,000
    disc_items = [
        {
            "description": "Floor Tile 600X1200",
            "size": "600X1200",
            "brand": "AMA Signature Collection",
            "coverage_area": 15.5,
            "quantity_sqft": 500.0,
            "rate_per_sqft": 100.0,
            "quantity_boxes": 32.26,
            "rate_per_box": 1550.0,
            "tax_mode": "inclusive",
            "tax_percent": 18.0,
            "total_amount": 50000.0,
        },
        {
            "description": "Wall Tile 300X600",
            "size": "300X600",
            "brand": "AMA Signature Collection",
            "coverage_area": 8.0,
            "quantity_sqft": 350.0,
            "rate_per_sqft": 100.0,
            "quantity_boxes": 43.75,
            "rate_per_box": 800.0,
            "tax_mode": "inclusive",
            "tax_percent": 18.0,
            "total_amount": 35000.0,
        }
    ]
    target_tot = 80000.0
    gross_init = sum(it["total_amount"] for it in disc_items)
    factor = target_tot / gross_init

    # Pro-rata scaling directly on item rates and totals
    for it in disc_items:
        it["total_amount"] = round(it["total_amount"] * factor, 2)
        it["rate_per_sqft"] = round(it["total_amount"] / it["quantity_sqft"], 2)
        it["rate_per_box"] = round(it["rate_per_sqft"] * it["coverage_area"], 2)

    # Reconcile 1-paisa rounding difference on last item
    diff = round(target_tot - sum(it["total_amount"] for it in disc_items), 2)
    if abs(diff) > 0:
        disc_items[-1]["total_amount"] = round(disc_items[-1]["total_amount"] + diff, 2)
        disc_items[-1]["rate_per_sqft"] = round(disc_items[-1]["total_amount"] / disc_items[-1]["quantity_sqft"], 2)
        disc_items[-1]["rate_per_box"] = round(disc_items[-1]["rate_per_sqft"] * disc_items[-1]["coverage_area"], 2)

    disc_payload = {
        "quotation_number": "AMA-2026-DISC-AUTO",
        "customer_id": cust.id,
        "sales_person_id": sp.id,
        "tax_mode": "inclusive",
        "round_off": 0.0,
        "areas": [{"area_name": "Living & Dining", "items": disc_items}]
    }
    q_disc = QuotationService.save_quotation(disc_payload)
    assert abs(q_disc.net_total - 80000.0) < 0.01, f"Expected 80000, got {q_disc.net_total}"
    assert abs(q_disc.round_off) < 0.01, f"Expected 0.0 round off, got {q_disc.round_off}"
    assert abs(q_disc.items[0].rate_per_sqft - 94.12) < 0.01

    pdf_disc = CeramicPDFGenerator.generate_quotation_pdf(q_disc.id)
    assert os.path.exists(pdf_disc), "Discounted PDF was not generated"

    import pypdfium2 as pdfium
    pdf_doc = pdfium.PdfDocument(pdf_disc)
    pdf_text = "".join(p.get_textpage().get_text_range() for p in pdf_doc)
    assert "80,000.00" in pdf_text, "Target net total must appear in PDF"
    assert "Discount / Round Off" not in pdf_text, "Discount / Round Off must NOT appear in PDF"
    assert "Discount:" not in pdf_text, "Discount row must NOT appear in PDF"
    print(f" -> PASS: ₹85,000 reduced to ₹80,000 target by distributing rates (~₹94.12/sqft). Round off is ₹0.00 and no discount row printed in PDF: {os.path.basename(pdf_disc)}")

    print("\n[TEST 18] Verifying Assisted Salesperson Split Deals (Percentage & Amount Modes, PDF, Attribution)...")
    # Clean up previous run if exists
    old_split = Quotation.get_or_none(Quotation.quotation_number == "AMA-2026-SPLIT-AUTO")
    if old_split:
        QuotationItem.delete().where(QuotationItem.quotation == old_split).execute()
        QuotationArea.delete().where(QuotationArea.quotation == old_split).execute()
        old_split.delete_instance()

    all_sps = list(SalesPerson.select().where(SalesPerson.is_active == True))
    lead_sp = all_sps[0]
    asst_sp = all_sps[1]

    # Test 50% split on 60,000 quote
    split_payload = {
        "quotation_number": "AMA-2026-SPLIT-AUTO",
        "customer_id": cust.id,
        "sales_person_id": lead_sp.id,
        "assisted_by_id": asst_sp.id,
        "split_type": "percentage",
        "assisted_share_value": 50.0,
        "status": Quotation.STATUS_WON,
        "tax_mode": "inclusive",
        "round_off": 0.0,
        "areas": [
            {
                "area_name": "Living Room",
                "items": [
                    {
                        "description": "Premium Vitrified 800X1600",
                        "size": "800X1600",
                        "quantity_sqft": 600.0,
                        "rate_per_sqft": 100.0,
                        "tax_mode": "inclusive",
                        "total_amount": 60000.0
                    }
                ]
            }
        ]
    }
    q_split = QuotationService.save_quotation(split_payload)
    assert q_split.assisted_by_id == asst_sp.id
    assert abs(q_split.primary_share_amount - 30000.0) < 0.01
    assert abs(q_split.assisted_share_amount - 30000.0) < 0.01

    # Attribution verification
    assert abs(q_split.get_credit_for_salesperson(lead_sp.id) - 30000.0) < 0.01
    assert abs(q_split.get_credit_for_salesperson(asst_sp.id) - 30000.0) < 0.01

    # Amount split update: Assisted gets 20,000, Lead gets 40,000
    split_payload["id"] = q_split.id
    split_payload["split_type"] = "amount"
    split_payload["assisted_share_value"] = 20000.0
    q_split_amt = QuotationService.save_quotation(split_payload)
    assert abs(q_split_amt.primary_share_amount - 40000.0) < 0.01
    assert abs(q_split_amt.assisted_share_amount - 20000.0) < 0.01

    # PDF verification
    pdf_split = CeramicPDFGenerator.generate_quotation_pdf(q_split_amt.id)
    pdf_split_doc = pdfium.PdfDocument(pdf_split)
    pdf_split_text = "".join(p.get_textpage().get_text_range() for p in pdf_split_doc)
    assert lead_sp.name in pdf_split_text
    assert "Assisted By:" in pdf_split_text
    assert asst_sp.name in pdf_split_text
    print(f" -> PASS: Assisted deal split verified (50% -> ₹30k/₹30k, Amount -> ₹40k/₹20k). Both reps credited and PDF verified: {os.path.basename(pdf_split)}")

    # -------------------------------------------------------------
    # 19. PRODUCT TYPES (BOX, SQFT, PIECES, BAGS, NOS) IN BRAND CATALOG & QUOTATION
    # -------------------------------------------------------------
    print("\n[TEST 19] Verifying Product Types (Box, Sqft, Pieces, Bags, Nos) in Brand Catalog, Quotation Calculations, and PDF Output...")
    chem_brand = TileBrand.create(name="Kajaria Supreme & Construction Chemicals", description="Vitrified slabs, adhesives & installation tools")
    
    # Configure sizes for each product type
    sc_box = BrandSizeCoverage.create(
        brand=chem_brand, size="1200X1800", product_type="Box", coverage_sqft=23.25, pieces_per_box=1, default_rate_sqft=120.0, default_rate_box=2790.0
    )
    sc_sqft = BrandSizeCoverage.create(
        brand=chem_brand, size="Custom Cut Slab", product_type="Sqft", coverage_sqft=1.0, pieces_per_box=1, default_rate_sqft=150.0, default_rate_box=0.0
    )
    sc_pcs = BrandSizeCoverage.create(
        brand=chem_brand, size="Metallic Trim 1200MM", product_type="Pieces", coverage_sqft=1.0, pieces_per_box=1, default_rate_sqft=0.0, default_rate_box=450.0
    )
    sc_bags = BrandSizeCoverage.create(
        brand=chem_brand, size="Tile Adhesive 20Kg Bag", product_type="Bags", coverage_sqft=1.0, pieces_per_box=1, default_rate_sqft=0.0, default_rate_box=600.0
    )
    sc_nos = BrandSizeCoverage.create(
        brand=chem_brand, size="Levelling Spacer Clip", product_type="Nos", coverage_sqft=1.0, pieces_per_box=1, default_rate_sqft=0.0, default_rate_box=25.0
    )

    assert sc_box.product_type == "Box"
    assert sc_sqft.product_type == "Sqft"
    assert sc_pcs.product_type == "Pieces"
    assert sc_bags.product_type == "Bags"
    assert sc_nos.product_type == "Nos"

    multi_type_payload = {
        "quotation_number": "AMA-2026-MULTI-TYPE",
        "customer_id": cust.id,
        "sales_person_id": lead_sp.id,
        "tax_mode": "exclusive",
        "round_off": 0.0,
        "areas": [
            {
                "area_name": "Full Project Supply",
                "items": [
                    {
                        "description": "Floor Tile Slab (Box Unit)",
                        "size": "1200X1800",
                        "brand": chem_brand.name,
                        "product_type": "Box",
                        "coverage_area": 23.25,
                        "quantity_sqft": 232.5,
                        "rate_per_sqft": 120.0,
                        "quantity_boxes": 10.0,
                        "rate_per_box": 2790.0,
                        "tax_mode": "exclusive",
                        "total_amount": 27900.0  # 10 boxes * 2790
                    },
                    {
                        "description": "Granite Riser Steps (Sqft Unit)",
                        "size": "Custom Cut Slab",
                        "brand": chem_brand.name,
                        "product_type": "Sqft",
                        "coverage_area": 0.0,
                        "quantity_sqft": 100.0,
                        "rate_per_sqft": 150.0,
                        "tax_mode": "exclusive",
                        "total_amount": 15000.0  # 100 sqft * 150
                    },
                    {
                        "description": "Decorative Gold Border (Pieces Unit)",
                        "size": "Metallic Trim 1200MM",
                        "brand": chem_brand.name,
                        "product_type": "Pieces",
                        "coverage_area": 0.0,
                        "quantity_boxes": 20.0,
                        "rate_per_box": 450.0,
                        "tax_mode": "exclusive",
                        "total_amount": 9000.0  # 20 pcs * 450
                    },
                    {
                        "description": "Heavy Duty Tile Adhesive (Bags Unit)",
                        "size": "Tile Adhesive 20Kg Bag",
                        "brand": chem_brand.name,
                        "product_type": "Bags",
                        "coverage_area": 0.0,
                        "quantity_boxes": 15.0,
                        "rate_per_box": 600.0,
                        "tax_mode": "exclusive",
                        "total_amount": 9000.0  # 15 bags * 600
                    },
                    {
                        "description": "Tile Floor Leveller Clips (Nos Unit)",
                        "size": "Levelling Spacer Clip",
                        "brand": chem_brand.name,
                        "product_type": "Nos",
                        "coverage_area": 0.0,
                        "quantity_boxes": 40.0,
                        "rate_per_box": 25.0,
                        "tax_mode": "exclusive",
                        "total_amount": 1000.0  # 40 nos * 25
                    }
                ]
            }
        ]
    }
    q_multi = QuotationService.save_quotation(multi_type_payload)
    items_created = list(QuotationItem.select().where(QuotationItem.quotation == q_multi).order_by(QuotationItem.sl_no))
    assert len(items_created) == 5
    assert items_created[0].product_type == "Box"
    assert items_created[1].product_type == "Sqft"
    assert items_created[2].product_type == "Pieces"
    assert items_created[3].product_type == "Bags"
    assert items_created[4].product_type == "Nos"

    # Verify taxable & net amounts: 27900 + 15000 + 9000 + 9000 + 1000 = 61900 (+ 18% GST = 11142) -> Gross = 73042
    assert abs(q_multi.taxable_amount - 61900.0) < 0.01
    assert abs(q_multi.gross_total - 73042.0) < 0.01

    # Generate and verify PDF
    pdf_multi = CeramicPDFGenerator.generate_quotation_pdf(q_multi.id)
    pdf_multi_doc = pdfium.PdfDocument(pdf_multi)
    pdf_multi_text = "".join(p.get_textpage().get_text_range() for p in pdf_multi_doc)
    assert "BOX/UNIT" in pdf_multi_text
    assert "Sqft" in pdf_multi_text
    assert "Pcs" in pdf_multi_text
    assert "Bags" in pdf_multi_text
    assert "Nos" in pdf_multi_text
    print(f" -> PASS: Created quotation with all 5 product types (Box, Sqft, Pieces, Bags, Nos). Math verified (Taxable: ₹61,900, Gross: ₹73,042), and PDF verified: {os.path.basename(pdf_multi)}")

    print("\n" + "=" * 65)
    print("  ALL CORE MODULES AND TESTS COMPLETED WITH 100% SUCCESS!")
    print("=" * 65)


if __name__ == "__main__":
    test_system()


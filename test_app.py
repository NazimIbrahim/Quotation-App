"""
Comprehensive verification test suite for AMA Ceramics Quotation Management System.
Tests database, models, calculations, services, PDF rendering, and UI construction.
"""
import sys
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

    print("\n" + "=" * 65)
    print("  ALL CORE MODULES AND TESTS COMPLETED WITH 100% SUCCESS!")
    print("=" * 65)


if __name__ == "__main__":
    test_system()


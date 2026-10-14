"""
Seed data generator for testing and demonstration.
Populates sales persons, customers, sample quotations across multiple areas, and payments.
"""
from datetime import date, timedelta
from app.database.connection import db
from app.database.models import (
    SalesPerson,
    Customer,
    Quotation,
    QuotationArea,
    QuotationItem,
    Payment,
    TileBrand,
    BrandSizeCoverage,
    init_database,
)


def seed_brands_and_sizes():
    """Seeds master tile brands with standard sizes and sqft coverage per box."""
    if TileBrand.select().count() > 0:
        return

    brand_data = [
        {
            "name": "Kajaria Eternity",
            "description": "Premium GVT/PGVT vitrified tiles and slabs",
            "sizes": [
                ("1200X1800", 23.25, 1, 145.0, 3371.25),
                ("800X1600", 27.56, 2, 115.0, 3169.40),
                ("600X1200", 15.50, 2, 88.0, 1364.00),
                ("600X600", 15.50, 4, 65.0, 1007.50),
                ("800X800", 20.66, 3, 92.0, 1900.72),
                ("300X600", 15.50, 8, 72.0, 1116.00),
            ]
        },
        {
            "name": "Simpolo Ceramics",
            "description": "Architectural vitrified surfaces & carving slabs",
            "sizes": [
                ("1200X1800", 23.25, 1, 150.0, 3487.50),
                ("1200X1200", 31.00, 2, 120.0, 3720.00),
                ("800X1600", 27.56, 2, 118.0, 3252.08),
                ("600X1200", 15.50, 2, 90.0, 1395.00),
                ("200X1200", 12.91, 5, 95.0, 1226.45),
                ("600X600", 15.50, 4, 68.0, 1054.00),
            ]
        },
        {
            "name": "Somany Ceramics",
            "description": "Slip shield & high abrasion vitrified tiles",
            "sizes": [
                ("800X1600", 27.56, 2, 112.0, 3086.72),
                ("600X1200", 15.50, 2, 85.0, 1317.50),
                ("600X600", 15.50, 4, 62.0, 961.00),
                ("300X600", 15.50, 8, 70.0, 1085.00),
                ("300X300", 8.71, 9, 55.0, 479.05),
            ]
        },
        {
            "name": "Qutone Ceramic",
            "description": "Italian designed i-marble slabs & quartz surfaces",
            "sizes": [
                ("1200X2400", 31.00, 1, 210.0, 6510.00),
                ("1200X1800", 23.25, 1, 165.0, 3836.25),
                ("800X1600", 27.56, 2, 125.0, 3445.00),
                ("600X1200", 15.50, 2, 95.0, 1472.50),
            ]
        },
        {
            "name": "Nexion Surfaces",
            "description": "Indo-Italian sintered porcelain slabs",
            "sizes": [
                ("1200X2400", 31.00, 1, 240.0, 7440.00),
                ("1200X1200", 31.00, 2, 160.0, 4960.00),
                ("800X1600", 27.56, 2, 138.0, 3803.28),
                ("600X1200", 15.50, 2, 105.0, 1627.50),
            ]
        },
        {
            "name": "AMA Signature Collection",
            "description": "Showroom hand-picked ultra luxury marble surfaces",
            "sizes": [
                ("1200X1800", 23.25, 1, 185.0, 4301.25),
                ("1200X1200", 31.00, 2, 135.0, 4185.00),
                ("800X1600", 27.56, 2, 135.0, 3720.60),
                ("600X1200", 15.50, 2, 98.0, 1519.00),
                ("200X1200", 12.91, 5, 95.0, 1226.45),
            ]
        },
        {
            "name": "CERA",
            "description": "Premium sanitaryware, faucets, basins & ceramic surfaces",
            "sizes": [
                ("Standard EWC/Basin", 1.0, 1, 0.0, 6500.0, "Pieces"),
                ("Table Top Basin", 1.0, 1, 0.0, 4200.0, "Pieces"),
                ("Wall Hung Closet", 1.0, 1, 0.0, 8500.0, "Pieces"),
                ("600X1200", 15.50, 2, 92.0, 1426.0, "Box"),
                ("600X600", 15.50, 4, 66.0, 1023.0, "Box"),
            ]
        }
    ]

    for b in brand_data:
        brand_obj = TileBrand.create(name=b["name"], description=b["description"])
        for item in b["sizes"]:
            sz = item[0]
            cov = item[1]
            pcs = item[2]
            r_sqft = item[3]
            r_box = item[4]
            ptype = item[5] if len(item) > 5 else "Box"
            BrandSizeCoverage.create(
                brand=brand_obj,
                size=sz,
                product_type=ptype,
                coverage_sqft=cov,
                pieces_per_box=pcs,
                default_rate_sqft=r_sqft,
                default_rate_box=r_box
            )


def seed_database(force=False):
    """Inserts sample realistic seed data into the database."""
    init_database()
    seed_brands_and_sizes()

    # Check if data already exists
    if not force and SalesPerson.select().count() > 0:
        return False

    with db.atomic():
        # Clear existing data if forced
        if force:
            Payment.delete().execute()
            QuotationItem.delete().execute()
            QuotationArea.delete().execute()
            Quotation.delete().execute()
            Customer.delete().execute()
            SalesPerson.delete().execute()
            BrandSizeCoverage.delete().execute()
            TileBrand.delete().execute()
            seed_brands_and_sizes()

        # 1. Seed Sales Team & Manager
        manager = SalesPerson.create(
            name="Rajesh Sharma",
            contact_number="+91 98250 12345",
            email="rajesh.sharma@amaceramics.com",
            role=SalesPerson.ROLE_MANAGER,
            monthly_target=2500000.0,
            is_active=True,
        )

        sp1 = SalesPerson.create(
            name="Ananya Verma",
            contact_number="+91 98791 67890",
            email="ananya.v@amaceramics.com",
            role=SalesPerson.ROLE_SALES,
            monthly_target=900000.0,
            is_active=True,
        )

        sp2 = SalesPerson.create(
            name="Vikram Patel",
            contact_number="+91 94280 55441",
            email="vikram.p@amaceramics.com",
            role=SalesPerson.ROLE_SALES,
            monthly_target=800000.0,
            is_active=True,
        )

        sp3 = SalesPerson.create(
            name="Pooja Hegde",
            contact_number="+91 97233 44112",
            email="pooja.h@amaceramics.com",
            role=SalesPerson.ROLE_SALES,
            monthly_target=700000.0,
            is_active=True,
        )

        # 2. Seed Customers
        cust1 = Customer.create(
            name="Dr. Priya Sengupta",
            mobile_number="+91 98980 11223",
            email="dr.priya.s@gmail.com",
            delivery_address="Bungalow No. 14, Whispering Meadows, Near Sterling City, Bopal, Ahmedabad - 380058",
            site_location="Bopal Villa Project",
            notes="Requires matching Italian marble patterns and anti-skid bathroom tiles.",
        )

        cust2 = Customer.create(
            name="Ar. Rohan Mehta (Studio Form & Space)",
            mobile_number="+91 98240 77889",
            email="rohan@studioformspace.com",
            delivery_address="Plot 302, Sector 8, Gandhinagar, Gujarat - 382007",
            site_location="Luxury Weekend Home",
            notes="Architectural specifier. High volume luxury slab orders.",
        )

        cust3 = Customer.create(
            name="Sunrise Infrastructure Ltd",
            mobile_number="+91 99090 33445",
            email="procurement@sunriseinfra.in",
            delivery_address="Commercial Arcade Site, S.P. Ring Road, Science City Circle, Ahmedabad - 380060",
            site_location="Commercial Commercial Galleria",
            notes="Bulk commercial vitrified flooring. GST invoiced.",
        )

        cust4 = Customer.create(
            name="Manav & Neha Kapoor",
            mobile_number="+91 97129 88990",
            email="manav.kapoor@outlook.com",
            delivery_address="A-1802, The Skylark Towers, Sindhu Bhavan Road, Bodakdev, Ahmedabad - 380054",
            site_location="4-BHK Penthouse",
            notes="Demanding high gloss mirror finish for living room and wooden plank for balcony.",
        )

        # 3. Seed Sample Quotation 1 (Won - Detailed Multi-Area)
        today = date.today()
        q1 = Quotation.create(
            quotation_number="AMA-2026-0001",
            quotation_date=today - timedelta(days=5),
            customer=cust1,
            sales_person=sp1,
            customer_name=cust1.name,
            customer_phone=cust1.mobile_number,
            delivery_address=cust1.delivery_address,
            sales_person_name=sp1.name,
            status=Quotation.STATUS_WON,
            gross_total=449230.0,
            round_off=-230.0,
            net_total=449000.0,
            project_name="Bopal Villa Renovation",
            special_notes="Includes delivery to site. Customer requested factory batch inspection.",
            approved_by=manager,
            approved_at=today - timedelta(days=4),
        )

        # Area 1: Ground Floor
        a1_1 = QuotationArea.create(quotation=q1, area_name="GROUND FLOOR - LIVING & DINING", display_order=1)
        QuotationItem.create(
            area=a1_1, quotation=q1, sl_no=1,
            description="OMBRA EMERALD ULTRA-SS HIGH GLOSS GVT",
            size="1200X1800",
            brand="AMA Signature Collection",
            coverage_area=23.25,
            quantity_sqft=1450.0, rate_per_sqft=145.0,
            quantity_boxes=62.4, rate_per_box=3371.25,
            total_amount=210250.0
        )
        QuotationItem.create(
            area=a1_1, quotation=q1, sl_no=2,
            description="STATUARIO GLOSSY CARVING VITRIFIED",
            size="1200X1200",
            brand="Simpolo Ceramics",
            coverage_area=31.00,
            quantity_sqft=800.0, rate_per_sqft=120.0,
            quantity_boxes=25.8, rate_per_box=3720.0,
            total_amount=96000.0
        )

        # Area 2: Kids Bathroom
        a1_2 = QuotationArea.create(quotation=q1, area_name="KIDS BATHROOM", display_order=2)
        QuotationItem.create(
            area=a1_2, quotation=q1, sl_no=3,
            description="AQUA AZUL MATT CERAMIC WALL",
            size="600X1200",
            brand="Kajaria Eternity",
            coverage_area=15.50,
            quantity_sqft=360.0, rate_per_sqft=88.0,
            quantity_boxes=23.2, rate_per_box=1364.0,
            total_amount=31680.0
        )
        QuotationItem.create(
            area=a1_2, quotation=q1, sl_no=4,
            description="CALACATTA WHITE SATIN ANTI-SKID FLOOR",
            size="600X600",
            brand="Somany Ceramics",
            coverage_area=15.50,
            quantity_sqft=180.0, rate_per_sqft=65.0,
            quantity_boxes=11.6, rate_per_box=1007.50,
            total_amount=11700.0
        )

        # Area 3: Master Bathroom
        a1_3 = QuotationArea.create(quotation=q1, area_name="MASTER BATHROOM", display_order=3)
        QuotationItem.create(
            area=a1_3, quotation=q1, sl_no=5,
            description="ARMANI GREY POLISHED CONTINUOUS VEIN",
            size="800X1600",
            brand="Nexion Surfaces",
            coverage_area=27.56,
            quantity_sqft=480.0, rate_per_sqft=115.0,
            quantity_boxes=17.4, rate_per_box=3169.40,
            total_amount=55200.0
        )
        QuotationItem.create(
            area=a1_3, quotation=q1, sl_no=6,
            description="ONYX CRYSTAL GOLD BOOKMATCH SLAB",
            size="1200X1800",
            brand="Qutone Ceramic",
            coverage_area=23.25,
            quantity_sqft=240.0, rate_per_sqft=185.0,
            quantity_boxes=10.3, rate_per_box=4296.25,
            total_amount=44400.0
        )

        # Payments for Q1
        Payment.create(
            quotation=q1,
            amount=200000.0,
            payment_mode=Payment.MODE_BANK,
            payment_date=today - timedelta(days=4),
            status=Payment.STATUS_CLEARED,
            reference_number="HDFC-NEFT-9921048",
            notes="50% Order Advance received via NEFT"
        )
        Payment.create(
            quotation=q1,
            amount=150000.0,
            payment_mode=Payment.MODE_CHEQUE,
            payment_date=today - timedelta(days=1),
            status=Payment.STATUS_CLEARED,
            reference_number="CHQ #004521 - SBI",
            notes="Second stage dispatch milestone payment cleared"
        )

        # 4. Seed Quotation 2 (In-Review with Areas: Bar Counter, Balcony, First Floor Bathroom)
        q2 = Quotation.create(
            quotation_number="AMA-2026-0002",
            quotation_date=today - timedelta(days=2),
            customer=cust2,
            sales_person=sp2,
            customer_name=cust2.name,
            customer_phone=cust2.mobile_number,
            delivery_address=cust2.delivery_address,
            sales_person_name=sp2.name,
            status=Quotation.STATUS_IN_REVIEW,
            gross_total=135540.0,
            round_off=-540.0,
            net_total=135000.0,
            project_name="Gandhinagar Weekend Villa",
            special_notes="Special 5% architect discount submitted to Store Manager for approval.",
        )

        a2_1 = QuotationArea.create(quotation=q2, area_name="BAR COUNTER", display_order=1)
        QuotationItem.create(
            area=a2_1, quotation=q2, sl_no=1,
            description="NERO MARQUINA MATT CARVING SURFACE",
            size="800X1600",
            quantity_sqft=180.0, rate_per_sqft=135.0,
            quantity_boxes=13.0, rate_per_box=1870.0,
            total_amount=24300.0
        )

        a2_2 = QuotationArea.create(quotation=q2, area_name="BALCONY", display_order=2)
        QuotationItem.create(
            area=a2_2, quotation=q2, sl_no=2,
            description="NATURAL TEAK WOODEN PLANK MATT",
            size="200X1200",
            quantity_sqft=320.0, rate_per_sqft=95.0,
            quantity_boxes=30.0, rate_per_box=1013.33,
            total_amount=30400.0
        )

        a2_3 = QuotationArea.create(quotation=q2, area_name="FIRST FLOOR BATHROOM", display_order=3)
        QuotationItem.create(
            area=a2_3, quotation=q2, sl_no=3,
            description="BOTTOCHINO BEIGE CLASSIC GLOSS",
            size="600X1200",
            quantity_sqft=580.0, rate_per_sqft=92.0,
            quantity_boxes=37.4, rate_per_box=1426.0,
            total_amount=53360.0
        )
        QuotationItem.create(
            area=a2_3, quotation=q2, sl_no=4,
            description="DARK EMPERADOR ACCENT FEATURE TILE",
            size="600X1200",
            quantity_sqft=250.0, rate_per_sqft=110.0,
            quantity_boxes=16.1, rate_per_box=1708.0,
            total_amount=27480.0
        )

        # 5. Seed Quotation 3 (Open status)
        q3 = Quotation.create(
            quotation_number="AMA-2026-0003",
            quotation_date=today - timedelta(days=1),
            customer=cust4,
            sales_person=sp3,
            customer_name=cust4.name,
            customer_phone=cust4.mobile_number,
            delivery_address=cust4.delivery_address,
            sales_person_name=sp3.name,
            status=Quotation.STATUS_OPEN,
            gross_total=240000.0,
            round_off=0.0,
            net_total=240000.0,
            project_name="Skylark Duplex Penthouse",
            special_notes="Sample tiles shown at showroom. Customer will finalize after architect review.",
        )
        a3_1 = QuotationArea.create(quotation=q3, area_name="GROUND FLOOR - LIVING ROOM", display_order=1)
        QuotationItem.create(
            area=a3_1, quotation=q3, sl_no=1,
            description="ROYAL STATUARIO SUPREME POLISHED",
            size="1200X1800",
            quantity_sqft=1200.0, rate_per_sqft=150.0,
            quantity_boxes=51.6, rate_per_box=3488.37,
            total_amount=180000.0
        )
        a3_2 = QuotationArea.create(quotation=q3, area_name="KIDS BATHROOM", display_order=2)
        QuotationItem.create(
            area=a3_2, quotation=q3, sl_no=2,
            description="PASTEL MINT SUBWAY CERAMIC",
            size="300X600",
            quantity_sqft=600.0, rate_per_sqft=100.0,
            quantity_boxes=62.0, rate_per_box=967.74,
            total_amount=60000.0
        )

        # Partial token advance
        Payment.create(
            quotation=q3,
            amount=50000.0,
            payment_mode=Payment.MODE_GPAY,
            payment_date=today - timedelta(days=1),
            status=Payment.STATUS_CLEARED,
            reference_number="UPI/GPAY/392019842",
            notes="Initial token booking amount"
        )
        Payment.create(
            quotation=q3,
            amount=30000.0,
            payment_mode=Payment.MODE_PHONEPE,
            payment_date=today,
            status=Payment.STATUS_PENDING,
            reference_number="UPI/PHONEPE/PendingCl",
            notes="Awaiting bank confirmation"
        )

        # 6. Seed Quotation 4 (Commercial Won)
        q4 = Quotation.create(
            quotation_number="AMA-2026-0004",
            quotation_date=today - timedelta(days=10),
            customer=cust3,
            sales_person=sp1,
            customer_name=cust3.name,
            customer_phone=cust3.mobile_number,
            delivery_address=cust3.delivery_address,
            sales_person_name=sp1.name,
            status=Quotation.STATUS_WON,
            gross_total=580000.0,
            round_off=-5000.0,
            net_total=575000.0,
            project_name="Commercial Galleria Foyer",
            special_notes="Commercial heavy-traffic vitrified full-body tile specified.",
            approved_by=manager,
            approved_at=today - timedelta(days=9),
        )
        a4_1 = QuotationArea.create(quotation=q4, area_name="GROUND FLOOR - MAIN ENTRANCE LOBBY", display_order=1)
        QuotationItem.create(
            area=a4_1, quotation=q4, sl_no=1,
            description="FULL BODY TECHNICAL VITRIFIED MATT",
            size="600X1200",
            quantity_sqft=5000.0, rate_per_sqft=116.0,
            quantity_boxes=322.5, rate_per_box=1798.45,
            total_amount=580000.0
        )
        Payment.create(
            quotation=q4,
            amount=575000.0,
            payment_mode=Payment.MODE_BANK,
            payment_date=today - timedelta(days=7),
            status=Payment.STATUS_CLEARED,
            reference_number="RTGS-ICICI-COMM-4412",
            notes="100% full settlement received prior to loading"
        )

    return True


if __name__ == "__main__":
    seed_database(force=True)
    print("Seed data created successfully.")

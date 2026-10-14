"""
Configuration and constants for AMA Ceramics Quotation Management System.
"""
import sys
import os
from pathlib import Path

APP_VERSION = "2.0.0"
APP_NAME = "Quotation App"

# Runtime directory resolution (dev vs frozen executable)
if getattr(sys, "frozen", False):
    EXE_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", EXE_DIR))

    # Test if executable directory is writable (portable or user folder)
    is_writable = False
    try:
        test_file = EXE_DIR / ".write_test"
        test_file.touch()
        test_file.unlink()
        is_writable = True
    except (PermissionError, OSError):
        is_writable = False

    if is_writable:
        DATA_DIR = EXE_DIR
    else:
        DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "AMA_Ceramics_Quotation"
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    BASE_DIR = DATA_DIR
    RESOURCE_DIR = BUNDLE_DIR
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR
    RESOURCE_DIR = BASE_DIR

DB_PATH = DATA_DIR / "ceramics_quotation.db"
OUTPUT_PDF_DIR = DATA_DIR / "output_pdfs"
OUTPUT_PDF_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_DIR = DATA_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Ensure essential assets exist in ASSETS_DIR if bundled separately
if RESOURCE_DIR != DATA_DIR and (RESOURCE_DIR / "assets").exists():
    import shutil
    for asset_file in (RESOURCE_DIR / "assets").glob("*.*"):
        target_file = ASSETS_DIR / asset_file.name
        if not target_file.exists():
            try:
                shutil.copy2(asset_file, target_file)
            except Exception:
                pass

# Company Branding & Header Details
COMPANY_CONFIG = {
    "name": "AMA CERAMICS PVT LTD",
    "tagline": "Architectural Surfaces, Vitrified Tiles & Luxury Sanitaries",
    "address_line1": "Showroom & Experience Center: Plot 48, Ceramic Industrial Corridor",
    "address_line2": "S.G. Highway, Ahmedabad - 380054, Gujarat, India",
    "phone": "+91 98250 12345 / +91 79 2654 8900",
    "email": "sales@amaceramics.com | info@amaceramics.com",
    "website": "www.amaceramics.com",
    "gstin": "24AAACA5678Q1Z4",
    "state": "Gujarat (Code: 24)",
}

# Bank Details for Payments
BANK_DETAILS = {
    "bank_name": "HDFC Bank Ltd",
    "account_name": "AMA CERAMICS PRIVATE LIMITED",
    "account_number": "50200088991234",
    "ifsc_code": "HDFC0001245",
    "branch": "Bodakdev - S.G. Highway Branch, Ahmedabad",
    "account_type": "Current Account",
}

# Signatory Defaults
SIGNATORIES = {
    "store_manager_title": "Store Manager",
    "store_manager_name": "Rajesh Sharma",
    "store_manager_phone": "+91 98250 12345",
    "sales_associate_title": "Showroom Sales Associate",
}

# Standard 13-Point Terms & Conditions
STANDARD_TERMS_AND_CONDITIONS = [
    "Prices quoted are ex-showroom/godown and valid for 15 days from the date of quotation.",
    "Ceramic and vitrified tiles are natural clay products; slight variation in shades, tones, and sizes is inherent to production and acceptable as per IS/ISO standards.",
    "Customers must inspect all material for shade matching and batch consistency before laying.",
    "Once tiles are fixed or laid with adhesive/mortar, NO complaints regarding shade, variation, or surface finish will be entertained.",
    "Standard industry transit breakage allowance of 2% to 3% applies and should be factored into order quantities.",
    "Delivery schedules are subject to warehouse stock availability and will be scheduled within 3 to 7 working days upon receipt of advance.",
    "Unloading, floor lifting, and site crane charges (if any) shall be strictly borne by the customer.",
    "Payment terms: Minimum 50% advance on confirmation, and 100% full settlement prior to final material dispatch.",
    "Returns are accepted within 15 days of delivery only for intact, unopened, factory-sealed boxes, subject to a 10% restocking charge.",
    "Loose, opened boxes, cut pieces, special-order imported slabs, and customized sizes are strictly non-returnable.",
    "GST and all statutory taxes are charged at prevailing government slabs (currently 18% on tiles).",
    "Any damage or shortage during customer-arranged transportation will not be the responsibility of AMA Ceramics Pvt Ltd.",
    "All disputes and claims arising under this quotation are subject exclusively to Ahmedabad jurisdiction only.",
]

# Standard Project Area Suggestions
DEFAULT_PROJECT_AREAS = [
    "Ground Floor - Living & Dining",
    "Kids Bathroom",
    "First Floor Bathroom",
    "Master Bathroom",
    "Guest Bathroom",
    "Kitchen & Utility",
    "Balcony",
    "Bar Counter",
    "Terrace & Outdoor Deck",
    "Facade & Elevation",
    "Pooja Room",
]

# Common Tile Sizes
COMMON_TILE_SIZES = [
    "1200X1800",
    "1200X1200",
    "800X1600",
    "600X1200",
    "600X600",
    "300X600",
    "300X300",
    "800X800",
    "200X1200 (Wood Plank)",
    "1200X2400 (Slab)",
]

"""
Configuration and constants for AMA Ceramics Quotation Management System.
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "ceramics_quotation.db"
OUTPUT_PDF_DIR = BASE_DIR / "output_pdfs"
OUTPUT_PDF_DIR.mkdir(parents=True, exist_ok=True)

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

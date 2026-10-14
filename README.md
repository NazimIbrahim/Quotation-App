# ✦ AMA Ceramics Pvt Ltd — Ceramic & Tile Quotation Management System (v2.0)

A standalone, modern desktop enterprise application built in Python for **AMA Ceramics Pvt Ltd** to streamline the lifecycle of ceramic and vitrified tile quotations, multi-area project estimation, payment tracking, salesperson target performance, and printable PDF generation.

---

## 🏛️ Application Architecture & Tech Stack

- **Frontend / GUI**: [CustomTkinter](https://customtkinter.tomschimansky.com/) (modern responsive dark/light desktop UI, high-DPI scaling on Windows).
- **Backend / ORM**: [Peewee ORM](http://docs.peewee-orm.com/) with SQLite (`ceramics_quotation.db`), featuring automatic schema creation and relationships with cascading deletes.
- **Printable Output**: [ReportLab](https://www.reportlab.com/) generating high-resolution printable PDF quotations with area subheaders, 13-point standard terms, bank details, and manager/sales signatures.
- **Analytics & Math**: Pure Python business logic with financial decimal precision, Indian currency word conversion, and metrics tracking.

---

## 📁 Modular Project Structure

```
d:\Quotation-App\
├── app/
│   ├── __init__.py
│   ├── config.py                 # Company branding, bank details, standard 13 terms & conditions
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py         # SQLite connection with WAL pragmas
│   │   ├── models.py             # SalesPerson, Customer, Quotation, QuotationArea, QuotationItem, Payment
│   │   └── seed_data.py          # Realistic seed data for salespersons, customers, multi-area quotes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── quotation_service.py  # Quotation numbering, calculations, multi-area logic & approvals
│   │   ├── payment_service.py    # Advances, GPay/PhonePe/Bank/Cheques, clearance & balances
│   │   ├── report_service.py     # Daily/Weekly/Monthly metrics, salesperson progress & receivables
│   │   └── pdf_service.py        # ReportLab PDF generator matching ceramic quotation layout
│   └── ui/
│       ├── __init__.py
│       ├── theme.py              # Visual colors, palette, status badges
│       ├── components/
│       │   ├── __init__.py
│       │   └── stat_card.py      # Reusable KPI metric widgets
│       ├── views/
│       │   ├── __init__.py
│       │   ├── dashboard_view.py       # Main dashboard: KPIs, targets, receivables & recent quotes
│       │   ├── quotation_list_view.py  # Quotation directory, search, status filters & PDF actions
│       │   ├── quotation_editor_view.py# Multi-area quote builder with brand/coverage calculations
│       │   ├── brand_catalog_view.py   # Tile Brands, Sizes & Coverage Area (Sqft/Box) catalog
│       │   ├── payment_view.py         # Payment tracking, clearance manager & global pending checks
│       │   ├── customer_view.py        # Customer CRM, addresses & quote history
│       │   ├── sales_team_view.py      # Sales targets, achievement progress & manager approvals
│       │   └── reports_view.py         # Daily/Weekly/Monthly reports with CSV export
│       └── app_window.py         # Main CustomTkinter window shell & navigation sidebar
├── output_pdfs/                  # High-resolution generated quotation PDFs
├── main.py                       # Application entry point with Windows High-DPI support
├── run.bat                       # 1-Click Windows launcher batch script
├── test_app.py                   # Automated end-to-end verification test suite
├── requirements.txt              # Production dependency specifications
└── README.md                     # Documentation & operational guide
```

---

## ⚡ Quick Start & Installation

### Option 1: 1-Click Windows Launcher (Recommended)
Double-click `run.bat` in the project root. It will automatically detect Python 3.11, set up the environment, and launch the application.

### Option 2: Command Line
```powershell
# Navigate to the project directory
cd D:\Quotation-App

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Option 3: Run the Test Suite
```powershell
python test_app.py
```

---

## 🚀 Key Modules & Capabilities

### 1. User Roles & Management
- **Role Switcher in Sidebar**: Easily toggle between **Rajesh Sharma (Store Manager)** and sales associates (**Ananya Verma**, **Vikram Patel**, **Pooja Hegde**) to test different operational perspectives.
- **Sales Person Profile**:
  - Name, contact phone, email.
  - Monthly Sales Target amount (in ₹).
  - Total Sales Achieved (calculated in real time from `Won` closed quotations).
  - Balance to target & percentage completed.
- **Manager Approval Workflow**:
  - Dedicated approval queue for quotations marked `In-Review` (e.g. special architect discounts).
  - One-click `Approve (Won)` or `Reject (Lost)` with audit log.
- **Customer CRM**:
  - Customer directory with mobile number, site location, delivery address.
  - Complete history of past quotations, net values, and clearance statuses.

### 2. Multi-Area Quotation Engine
- **Header Information**:
  - Auto-generated sequential quotation numbering (`AMA-2026-0001`, `AMA-2026-0002`, ...).
  - Quotation date, client selector with quick-add popup, contact phone, site location, delivery address, and sales associate name.
- **Project Section / Area Grouping**:
  - Items are grouped by physical project areas:
    - *Ground Floor - Living & Dining*
    - *Kids Bathroom*
    - *Master Bathroom*
    - *First Floor Bathroom*
    - *Balcony*
    - *Bar Counter*
    - *Custom Areas*
  - Add or remove unlimited areas; add or remove tile items inside each area.
- **Item Fields & Bidirectional Auto-Calculations (10 Columns)**:
  - **1. Sl. No**: Auto-numbered across sections.
  - **2. Description**: e.g., `OMBRA EMERALD ULTRA-SS`, `STATUARIO GLOSSY CARVING`, `NERO MARQUINA MATT`.
  - **3. Size**: Dropdown containing **Brand-Wise Sizes Only** for the selected brand (e.g. selecting `Kajaria Eternity` displays only Kajaria's sizes including `1200X1800 15MM`). Includes inline `+ Add New Size...` shortcut to add new sizes on the fly.
  - **4. Brand**: Dropdown populated with showroom brands (`Kajaria Eternity`, `Simpolo Ceramics`, `Somany Ceramics`, etc.). Switching brands dynamically re-filters the Size dropdown strictly to that brand's sizes.
  - **5. Coverage Area (Sqft/Box)**: Exact square footage covered per box (e.g. `23.25` for 1200x1800 15MM, `19.37` for 600x1200). Auto-populated when Brand and Size are selected, or custom editable.
  - **6. Quantity in Sqft**: Auto-calculated when Boxes is entered (`Boxes × Coverage`), or manually entered.
  - **7. Rate per Sqft (₹)**: Auto-calculated from Box Rate (`Rate/Box ÷ Coverage`), or manually entered.
  - **8. Quantity in Boxes**: Auto-calculated from Sqft (`Sqft ÷ Coverage`), or manually entered.
  - **9. Rate per Box (₹)**: Auto-calculated from Sqft Rate (`Rate/Sqft × Coverage`), or manually entered.
  - **10. Total Amount (₹)**: Auto-calculated dynamically (`Sqft × Rate/Sqft` or `Boxes × Rate/Box`).
  - **Bidirectional Calculation Engine**: Typing Sqft updates Boxes and Box Price; typing Boxes updates Sqft and Sqft Rate; changing Coverage updates both proportionally.
- **Financial Totals Section**:
  - **Gross Total**: Sum of all line items across all project areas.
  - **Round Off / Discount**: Positive or negative adjustment entry with live net total recalculation.
  - **Net Total Payable**: Prominently displayed with Indian Rupee formatting.

### 3. Payment Tracking & Receivables
- **Quotation Statuses**:
  - `Open`: Active quote presented to client.
  - `In-Review`: Submitted for manager approval / special discounts.
  - `Won`: Closed deal; ready for dispatch / milestone fulfillment.
  - `Lost`: Cancelled or declined.
- **Payment Modes**:
  - `GPay`, `PhonePe`, `Bank Transfer (NEFT/RTGS/IMPS)`, `Cheque`, `Cash`.
- **Clearance Management**:
  - Mark entries as `Pending` or `Cleared`.
  - **Global Pending Clearance Queue**: Pinpoints all uncleared cheques and UPI tokens across the entire showroom with 1-click clearance.
- **Outstanding Balance**:
  - Automatically calculates: `Net Total - Cleared Payments`.
  - Displays payment fulfillment status: `Fully Paid`, `Partially Paid`, or `Unpaid`.

### 4. Executive Reporting & Analytics
- **Timeframe Filters**: Filter by **Daily**, **Weekly**, **Monthly**, or **All-Time**.
- **Sales Targets vs. Achievement Progress**: Individual and team-wide animated progress bars with percentage completion badges.
- **Receivables Breakdown**:
  - Bank Realized collections vs. Pending Cheques vs. Outstanding receivables.
  - Quotation conversion rates (Won / Total Quotes).
- **Export**: One-click export to CSV spreadsheet (`sales_report_export.csv`).

### 5. Official PDF Quotation Specification (ReportLab)
- **Company Branding Header**:
  - Company: **AMA CERAMICS PVT LTD**
  - Subtitle: *Architectural Surfaces, Vitrified Tiles & Luxury Sanitaries*
  - Address, GSTIN, State Code 24 (Gujarat), Phone, Email & Website.
- **Customer & Site Details Block**:
  - Bill To / Deliver To name, phone, site delivery address, project reference, quotation number, date, and valid till date.
- **Structured 10-Column Item Table**:
  1. `Sl.`
  2. `Description`
  3. `Size`
  4. `Brand`
  5. `Coverage (Sqft/Bx)`
  6. `Quantity in Sqft`
  7. `Rate Per Sqft (₹)`
  8. `Quantity in Boxes`
  9. `Rate Per Box (₹)`
  10. `Total Amount (₹)`
- **Full-Width Area Subheaders**:
  - Distinct dark slate rows spanning all 10 columns: `✦ AREA: KIDS BATHROOM`, `✦ AREA: GROUND FLOOR - LIVING & DINING`, etc.
- **Right-Aligned Financial Summary**:
  - Gross Total, Round Off / Discount, and Net Total Payable with Indian Currency amount in words.
- **Bank Payment Details Block**:
  - Bank account number, IFSC code, account name, branch, and digital QR/UPI modes.
- **Standard 13-Point Terms & Conditions**:
  - Formatted 2-column legal-grade terms covering tile shade/batch variations, breakage allowance (2-3%), laying inspection clauses, unloading terms, 50% advance, and return policies.
- **Dual Signatures Block**:
  - **Store Manager** & **Showroom Sales Associate** with customer acceptance signature block.

### 6. In-App Company & PDF Settings Manager (New!)
Navigate to **⚙️ Company & PDF Settings** in the left sidebar to manually edit any data that appears on the quotation PDF:
- **🏢 Company Branding**: Edit Company Name, Tagline, Showroom Address Line 1 & 2, Phone numbers, Email, Website, GSTIN, and State code.
- **🖼️ Company Logo Upload**: Browse and upload your custom showroom logo (`PNG`, `JPG`, `JPEG`). The image is automatically scaled and rendered cleanly at the top-left of the PDF!
- **🏦 Bank & Payment Accounts**: Edit Bank Name, Beneficiary Name, Account Number, IFSC, Branch, Account Type, and UPI/remittance notes.
- **✍️ Signatures & Authority**: Customize the Store Manager title, name, phone, and Sales Associate designation.
- **📜 Terms & Conditions**: In-app editor for all quotation legal clauses with full add/edit/delete support and a 1-click restore to standard 13-point ceramic terms.
- **Live Preview & Persistence**: Click **"📄 Preview PDF"** to instantly test and see your updated company details, logo, and terms rendered in a real PDF. All settings are persistently saved to the SQLite database.

### 7. Tile Brands & Coverage Master Catalog (New!)
Navigate to **🏷️ Brands & Coverage** in the left sidebar to manage tile brands, sizes, and packaging coverage:
- **🏷️ Tile Brands Management**: Add, edit, or toggle active status for ceramic tile brands (e.g. Kajaria Eternity, Simpolo Ceramics, Somany, Qutone, Nexion, AMA Signature Collection, or your own showroom brands).
- **📐 Sizes & Packaging Specifications**:
  - Configure standard or custom tile sizes (`1200X1800`, `800X1600`, `600X1200`, `600X600`, etc.).
  - Set exact **Coverage Area per Box (Sqft)** (e.g., `23.25` sqft/box for 1200x1800 2-piece boxes, `19.37` sqft/box for 600x1200 2-piece boxes).
  - Set **Pieces per Box**, **Default Rate per Sqft (₹)**, and **Default Box Price (₹)**.
- **⚡ Quotation Builder Integration**:
  - **Brand-Wise Sizes Only**: Selecting a Brand strictly filters the Size dropdown to show ONLY that brand's configured sizes (no clutter from other brands).
  - **Real-Time Auto-Update**: When you add a new size (e.g. `1200X1800 15MM`) in the Brands catalog, it is automatically and immediately available in the Size dropdown on click without requiring app restarts or manual sync.
  - **Inline Quick-Add**: Select `+ Add New Size...` directly in any item row's Size dropdown to add a new packaging size on the fly.
  - **Auto-Calculations**: Selecting Brand and Size auto-fills the exact Coverage Area (Sqft/Box), default rates, and live box/sqft calculations.

### 8. What's New in Version 2.0 (v2.0 Release Highlights)
- 📦 **Multi-Unit Product Types**: Full native support for **Box**, **Sqft**, **Pieces**, **Bags**, and **Nos** in Brand catalogs, quotation rows, calculations, and PDF generation (`QTY (BOX/UNIT)`).
- 🔒 **Encrypted Quotation Export**: 1-click masked quote PDF (`[🔒 Enc]`) generating 4-5 random letter AMA codes (e.g. `HSDS-AMA`) with brand names stripped, strictly preserving original database records.
- 🎯 **Smart Lump-Sum Discounting with CERA Exclusion**: Distribute overall lump-sum discounts evenly across item rates so the final customer PDF displays clean rates without negative discount lines, while strictly leaving CERA brand items at 0% discount.
- 👥 **Assisted Salesperson Collaboration & Deal Splits**: Assign secondary sales executives with custom percentage or fixed-amount commission splits. Both reps appear on quotes and earn proper target achievement credit.
- 📊 **Periodic Quotations Audit & Filtered Export**: Export quotations filtered by time period (Today, This Week, This Month, Last Month, Last 30 Days, This Year, All Time, or Custom), Salesperson, and Status (`Only Won`, `Only Open`, `Only In-Review`, `Only Lost`) to executive PDF or CSV.
- 🔍 **Customer Auto-Popup & Phone Match**: Typing a customer's phone or name automatically searches the database and populates delivery address, site, and profile.
- ⚡ **High-Performance Architecture**: SQLite WAL mode, composite indexes, 64MB cache, memory-mapped I/O, and batch pre-fetching for instant response times.

---

## 🗄️ Preloaded Demo Seed Data

The application comes preloaded with ready-to-test data:

1. **Team Members**:
   - `Rajesh Sharma` (Store Manager, Target: ₹25,00,000)
   - `Ananya Verma` (Sales Associate, Target: ₹9,00,000)
   - `Vikram Patel` (Sales Associate, Target: ₹8,00,000)
   - `Pooja Hegde` (Sales Associate, Target: ₹7,00,000)

2. **Customers**:
   - `Dr. Priya Sengupta` (Whispering Meadows Villa, Bopal)
   - `Ar. Rohan Mehta` (Studio Form & Space, Gandhinagar)
   - `Sunrise Infrastructure Ltd` (Commercial Galleria, S.P. Ring Road)
   - `Manav & Neha Kapoor` (The Skylark Towers, Sindhu Bhavan Road)

3. **Sample Quotations**:
   - `AMA-2026-0001` (Status: Won, Net: ₹4,49,000) — Multi-area quote covering *Ground Floor Living*, *Kids Bathroom*, and *Master Bathroom* with OMBRA EMERALD, STATUARIO, and ONYX CRYSTAL slabs.
   - `AMA-2026-0002` (Status: In-Review, Net: ₹1,35,000) — *Bar Counter* (NERO MARQUINA), *Balcony* (TEAK PLANK), *First Floor Bathroom* (BOTTOCHINO).
   - `AMA-2026-0003` (Status: Open, Net: ₹2,40,000) — *Kids Bathroom & Living Room*.
   - `AMA-2026-0004` (Status: Won, Net: ₹5,75,000) — Bulk commercial full-body tiles.

---

## 💾 Installation on Another PC (No Python Required)

The application is fully bundled as a standalone Windows desktop distribution. **No Python installation or command line knowledge is required on the target computer.**

### Option 1: Official Windows Installer (Recommended)
1. Download **[`AMA_Ceramics_Quotation_Setup_v2.0.exe`](https://github.com/NazimIbrahim/Quotation-App/releases/download/v2.0/AMA_Ceramics_Quotation_Setup_v2.0.exe)** from [GitHub Releases v2.0](https://github.com/NazimIbrahim/Quotation-App/releases/tag/v2.0).
2. Double-click `AMA_Ceramics_Quotation_Setup_v2.0.exe` to run the setup wizard.
3. Choose your installation location (defaults to your user profile or Program Files without requiring admin elevation).
4. Check **Create Desktop Icon**.
5. Click **Install**.
6. The setup wizard creates a desktop shortcut with the official AMA Ceramics icon and launches the system immediately.

### Option 2: Standalone Portable Executable
1. Download **[`AMA_Ceramics_Quotation.exe`](https://github.com/NazimIbrahim/Quotation-App/releases/download/v2.0/AMA_Ceramics_Quotation.exe)**.
2. Double-click `AMA_Ceramics_Quotation.exe` to launch directly from any folder or USB drive.

### Building the Setup Installer from Source
To recompile the standalone binary and setup installer at any time:
```cmd
build_setup.bat
```
This runs the full PyInstaller compilation and Inno Setup package generator in `dist_installer/`.


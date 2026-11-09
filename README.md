# MarketMate – Grocery Store Inventory, POS & Business Intelligence System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework: Flask](https://img.shields.io/badge/Framework-Flask_3.1-black.svg)](https://flask.palletsprojects.com/)
[![Database: SQLite](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![Visualization: Plotly](https://img.shields.io/badge/Visualizations-Plotly.js-orange.svg)](https://plotly.com/)
[![Tests: Pytest](https://img.shields.io/badge/Tests-35%20Passed-brightgreen.svg)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, full-stack retail management web application built with **Python Flask**, **SQLite**, **Pandas**, **Plotly**, and **Bootstrap 5**. Designed specifically for modern supermarkets and specialty grocery retailers, **MarketMate** delivers a unified operations center spanning Point of Sale (POS), real-time stock control, supplier relationship management, and high-impact business intelligence analytics.

---

## 🎨 Distinctive Visual Identity

Unlike conventional generic green grocery templates, MarketMate introduces a **curated warm palette** reflecting premium retail craft and clarity:

| Element | Color Hex | Visual Purpose |
|---|---|---|
| **Primary Background** | `#F4EFE6` (Warm Ivory) | Reduces eye strain during long cashier and management shifts |
| **Sidebar & Structure**| `#17263C` (Deep Navy) | Authoritative structure, collapsible navigation, high contrast |
| **Primary Accent** | `#D97945` (Terracotta) | Primary calls-to-action, alerts, active states, key financial KPIs |
| **Secondary Accent** | `#8DA285` (Muted Sage) | Positive status pills, inventory health badges, subtle borders |
| **Typography** | Inter & Manrope | Ultra-clean, modern geometric numerals and readable tabular data |

---

## ✨ Core Features & Functional Scope

### 1. 🔐 Authentication & Role-Based Access Control (RBAC)
- **Two Distinct System Roles**:
  - `ADMIN`: Unrestricted access across catalog management, vendor relationships, manual inventory adjustments, audit trails, user administration, and financial BI reports.
  - `CASHIER`: Focused workflow restricted to the Point of Sale (POS) terminal, live catalog lookup, transaction processing, receipt generation, and permitted sales history.
- Cryptographic password hashing via **Werkzeug** (`pbkdf2:sha256`).
- Secure session management and route protection decorators (`@login_required`, `@role_required(['ADMIN'])`).
- Automatic prevention against deleting the sole remaining active administrator.

### 2. 🛒 Point of Sale (POS) Terminal
- **Fast Barcode & Autocomplete Search**: Real-time live filtering by name, SKU barcode scanner compatibility, and category filter pills.
- **Dynamic Interactive Cart**: Live line-item quantity adjusters (`+`, `-`, manual entry), subtotal computation, and line item removal.
- **Discount & Tax Engines**: Supports percentage-based (%) or flat dollar ($) discounts with real-time recalculation preview and configurable sales tax (default: 5.0%).
- **Multi-Method Tender**:
  - **Cash**: Automated tendered amount validation, quick-cash chips ($10, $20, $50, $100, Exact), and live change return calculator.
  - **Card**: Seamless digital card swipe/tap capture.
  - **UPI**: Integrated QR code preview and payment reference logging.
- **Strict Backend Price Enforcement**: Frontend submissions only provide `{product_id, quantity}`. Prices submitted by clients are completely discarded; the database is the single source of truth.
- **Print-Friendly Invoice**: Formatted thermal receipt layout with store details, unique sequential invoice IDs (`INV-YYYYMMDD-XXXX`), and `@media print` styling.

### 3. 📦 Product & Catalog Management
- Full CRUD operations with comprehensive boundary validation:
  - Universal SKU uniqueness enforcement.
  - Strict price bounds (`cost_price >= 0`, `selling_price >= 0`, `quantity >= 0`).
  - Stock threshold monitoring with status indicators: *In Stock*, *Low Stock*, *Out of Stock*, *Expiring Soon*, and *Expired*.
  - Categorization across fresh produce, dairy & eggs, bakery, beverages, grains & pantry, meat & deli, snacks, and canned goods.
  - Linked vendor tracking and perishable expiry date scheduling.

### 4. 🏢 Supplier Management
- Comprehensive vendor directory with contact persons, telephone numbers, email addresses, delivery addresses, and purchasing notes.
- Automatic counting of supplied products with detailed profile views.
- Referential integrity protections on supplier deletion (`ON DELETE SET NULL`).

### 5. 📊 Real-Time Inventory Control & Audit Trail
- **Atomic Stock Adjustments**: Restock receipts (`PURCHASE_RECEIPT`), audit corrections (`STOCK_ADJUSTMENT`), damaged goods write-offs (`DAMAGE`), expiration write-downs (`EXPIRY`), and customer returns (`RETURN`).
- **Negative Stock Prevention**: Prevents inventory from ever dropping below zero with rollback guarantees.
- **Immutable Audit Trail (`stock_movements`)**: Logs timestamp, product, movement classification, quantity delta, prior stock, new stock, reference ID, and initiating staff member.
- **Automated Reorder Planning**: Calculates required replenishment volume based on safety stock deficits (`recommended_reorder = max(2 * min_stock - current_qty, 10)`), with unit cost estimates and vendor phone links.

### 6. 📈 Business Intelligence Dashboard (Plotly & Pandas)
- High-level KPI cards: *Net Sales Revenue*, *Average Order Value (AOV)*, *Total Inventory Valuation (Cost & Retail)*, and *Critical Action Items*.
- **Interactive Plotly Visualizations**:
  1. **Daily Revenue Trend**: Smooth area spline chart tracking daily revenue trajectory.
  2. **Sales by Product Category**: Interactive donut chart showcasing category revenue share.
  3. **Top 10 Selling Products**: Horizontal bar chart comparing product revenue performance.
  4. **Payment Method Breakdown**: Comparative volume analysis (Cash vs. Card vs. UPI).
  5. **Monthly Sales Comparison**: Historical month-over-month revenue bars.
  6. **Inventory Valuation by Category**: Grouped bar chart juxtaposing cost investment against retail shelf value.
- Responsive date filters: *Today*, *Last 7 Days*, *Last 30 Days*, *This Month*, *All Time*, and custom date pickers.

### 7. 📑 Dedicated Financial Reports & RFC4180 CSV Export
- **Daily Sales Report**: Daily turnover, discounts, tax collected, and payment breakdowns.
- **Monthly Sales Report**: Month-by-month financial turnover, order counts, and AOV.
- **Product Profitability Report**: Accurate Cost of Goods Sold (COGS), gross profit, and margin % calculations utilizing historical snapshot pricing from `sale_items`.
- **Low Stock Reorder Report**: Actionable procurement schedule for supplier purchase orders.
- **Expiry Monitoring Report**: Proactive spillage prevention tracking perishables expiring in under 30 days and retail value at risk.
- **Full Sales Ledger**: Audit log of all invoices with customer details and line items.
- **One-Click CSV Export**: Every report streams compliant CSV files directly to the browser.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+ & Flask 3.1 (Application Factory, Blueprints, Context Processors, Custom Jinja Filters)
- **Database**: SQLite 3 with Foreign Key Enforcement (`PRAGMA foreign_keys = ON;`)
- **Data Processing**: Pandas 3.0
- **Data Visualization**: Plotly 7.1 (Plotly.js via dynamic JSON serialization)
- **Frontend**: HTML5, CSS3, JavaScript (ES6 Fetch API), Bootstrap 5.3, Bootstrap Icons
- **Authentication**: Werkzeug Password Hashing (`generate_password_hash`, `check_password_hash`)
- **Testing**: Pytest 9.2 (35 automated unit, integration, and security tests)

---

## 🏗️ Project Architecture

```
GreenLeaf/
├── app/
│   ├── __init__.py               # Flask application factory (create_app)
│   ├── database.py               # SQLite connection manager, DDL schema, transactions
│   ├── models/                   # Data structures
│   ├── services/                 # Dedicated business logic layer
│   │   ├── auth_service.py       # Authentication, password hashing, RBAC decorators
│   │   ├── product_service.py    # Product CRUD, catalog queries, stock status logic
│   │   ├── supplier_service.py   # Supplier directory and portfolio tracking
│   │   ├── inventory_service.py  # Stock adjustments, audit trails, reorder formulas
│   │   ├── pos_service.py        # Authoritative billing, cart calculations, atomic sales
│   │   ├── analytics_service.py  # KPI metrics & Plotly chart builders
│   │   └── report_service.py     # Financial reports, COGS, margins, CSV streaming
│   ├── routes/                   # Flask Blueprint controllers
│   │   ├── auth.py               # Sign in, sign out, user profile
│   │   ├── dashboard.py          # BI Dashboard with Plotly visuals
│   │   ├── products.py           # Catalog routes & live search API
│   │   ├── suppliers.py          # Supplier directory routes
│   │   ├── inventory.py          # Stock monitoring, adjustment modal, movements
│   │   ├── pos.py                # POS interface, checkout API, receipt generation
│   │   ├── reports.py            # Reports hub & CSV download endpoints
│   │   └── users.py              # Staff accounts administration
│   ├── static/
│   │   ├── css/
│   │   │   ├── custom.css        # Warm ivory, navy, terracotta design system
│   │   │   └── print-invoice.css # @media print receipt stylesheet
│   │   └── js/
│   │       ├── main.js           # Navigation, flash auto-dismiss, delete confirmations
│   │       ├── pos.js            # Interactive POS cart engine & checkout handler
│   │       └── analytics.js      # Plotly chart renderer & auto-resizer
│   └── templates/                # Jinja2 HTML templates
│       ├── base.html             # Fixed navy sidebar, header, global notifications
│       ├── auth/                 # Sign in & profile views
│       ├── dashboard/            # Business intelligence dashboard
│       ├── products/             # Product list & creation/edit form
│       ├── suppliers/            # Supplier list, detail & form
│       ├── inventory/            # Stock levels, movements, reorders, expiries
│       ├── pos/                  # POS screen, receipt invoice, sales history
│       ├── reports/              # Report center & individual report templates
│       ├── users/                # User accounts management
│       └── errors/               # 403, 404, 500 error pages
├── docs/
│   ├── ARCHITECTURE.md           # System architecture & design documentation
│   ├── DATABASE.md               # Detailed relational schema & ER diagram
│   └── API_AND_SECURITY.md       # API specs & threat mitigation matrix
├── tests/                        # Comprehensive Pytest test suite
│   ├── conftest.py               # Isolated test database fixtures & clients
│   ├── test_auth.py              # Authentication & RBAC test cases
│   ├── test_products.py          # Product CRUD & validation tests
│   ├── test_suppliers.py         # Supplier management tests
│   ├── test_inventory.py         # Stock adjustment & audit tests
│   ├── test_pos.py               # POS calculations, payments & invoice tests
│   ├── test_security.py          # Price tampering & SQL injection defense tests
│   ├── test_analytics.py         # Plotly generation & KPI metrics tests
│   └── test_reports.py           # Financial formulas & CSV export tests
├── config.py                     # Environment configurations
├── run.py                        # Entrypoint script
├── seed_data.py                  # Realistic grocery catalog & 30-day sales generator
├── requirements.txt              # Production & development dependencies
├── pytest.ini                    # Test runner configuration
├── .env.example                  # Sample environment variables
├── .gitignore                    # Version control exclusions
├── LICENSE                       # MIT License
└── README.md                     # Project documentation
```

---

## ⚡ Quick Start & Installation

### 1. Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed on your machine.
- Git (optional).

### 2. Clone or Navigate to the Project Directory
```bash
cd "path/to/GreenLeaf"
```

### 3. Set Up a Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Initialize & Seed Database with Realistic Demo Data
The application includes a rich database seeder featuring **37 grocery products**, **6 verified suppliers**, and **55 multi-item sales transactions** spread over the past 30 days:
```bash
python seed_data.py
```

### 6. Run the Application
```bash
python run.py
```
Open your web browser and navigate to:
**`http://localhost:5000`** (or `http://127.0.0.1:5000`)

---

## 🔑 Demo Credentials

| Role | Username | Password | Privileges |
|---|---|---|---|
| **Administrator** | `admin` | `Admin@123` | **Full access**: Dashboard, products, suppliers, inventory adjustments, POS, reports, staff management |
| **Cashier** | `cashier` | `Cashier@123` | **Operations**: POS checkout, barcode scan, product catalog (read-only), permitted receipts |
| **Cashier 2** | `maya_cashier` | `Cashier@123` | **Operations**: Secondary checkout counter |

> **Pro Tip**: The login page includes interactive one-click credentials chips to automatically populate username and password for rapid testing.

---

## 🧪 Running Automated Tests

MarketMate contains an exhaustive Pytest suite covering **35 test cases** across security, authentication, atomic billing, calculations, and CSV exports:

```bash
python -m pytest
```

### Test Suite Coverage Highlights
- ✅ **Authentication**: Password hashing verification, session lifecycle, failed attempts, and inactive user rejection.
- ✅ **Role-Based Access Control**: Validates that Cashiers receive `403 Forbidden` on admin-only routes (users, suppliers, inventory adjustments, reports).
- ✅ **Product Management**: CRUD validation, duplicate SKU rejection, and non-negative price/stock assertions.
- ✅ **POS Calculations & Discounts**: Exact subtotal, percentage discounts, fixed discounts, discount boundary validation (cannot exceed 100% or subtotal), sales tax calculations, cash tendered checks, and change return formulas.
- ✅ **Security / Price Tampering Defense**: Submitting manipulated `unit_price` in the cart payload is proven to be ignored; the database price is strictly applied.
- ✅ **Security / SQL Injection**: Parameterization tests across search inputs, category filters, and date filters.
- ✅ **Inventory Integrity**: Verification of atomic stock deductions on sale, atomic replenishment on adjustments, and negative stock denial.
- ✅ **Analytics & Plotly**: Validates JSON serializability of all 6 interactive charts.
- ✅ **Financial Reports & CSV**: Validates COGS, gross profits, margin percentages, and RFC4180 CSV file downloads.

---

## 🖼️ Application Walkthrough & Screenshots

### 1. Business Intelligence Dashboard
- **Top Metric Cards**: Displaying Net Revenue, Average Order Value (AOV), Retail Inventory Valuation, and Action Items with custom terracotta/sage accent styling.
- **Plotly Visualizations**: Interactive Area Revenue Trend, Donut Category Sales, Horizontal Bar Top 10 Selling Products, Payment Method Distribution, Historical Monthly Turnover, and Inventory Valuation.
- **Operational Feeds**: Live feeds of recent transactions and critical stock warnings.

### 2. Point of Sale (POS) Terminal
- **Split Layout**: Left side displays live catalog search, category pills, and responsive product cards with stock badges.
- **Cart Management**: Real-time quantity adjustments, discount controls, tax computation, and bold payable total.
- **Checkout Panel**: One-click Cash (with quick buttons and change due calculation), Card, and UPI methods.
- **Receipt Print View**: Dedicated print-friendly thermal receipt view with store address, barcode aesthetic, and itemized ledger.

### 3. Inventory Monitoring & Stock Adjustments
- **Stock Audit Table**: Clear visual indication of shelf quantities vs. minimum safety thresholds.
- **Stock Adjustment Modal**: Enables logging additions, damages, expirations, and audit corrections with required justification.
- **Reorder Planning**: Automated reorder recommendations with estimated cost calculations and vendor contact information.
- **Expiry Watch**: Categorizes perishables into *Expired*, *Expires Today*, and *Expiring Soon* with retail value at risk.

### 4. Reports & CSV Export Center
- Filterable tables for Daily Sales, Monthly Sales, Product Profitability (COGS & Margins), Low Stock Reorders, Expiry Monitoring, and Full Sales Ledger.
- Instant CSV export buttons on every report.

---

## 🚀 Future Roadmap

- [ ] Barcode label printing for newly added products.
- [ ] Email delivery of receipts directly to customers via SMTP.
- [ ] Multi-store synchronization and warehouse transfer requests.
- [ ] Machine learning sales forecasting utilizing historical seasonal data.

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

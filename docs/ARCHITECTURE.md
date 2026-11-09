# MarketMate System Architecture

## 1. Architectural Overview

**MarketMate – Grocery Store Inventory, POS & Business Intelligence System** is engineered following clean architectural principles:

```
┌────────────────────────────────────────────────────────┐
│                   Web Client (Browser)                 │
│   HTML5 / CSS3 (Warm Ivory, Navy, Terracotta) / JS     │
│       Plotly.js Interactive Visualizations / POS       │
└───────────────────────────▲────────────────────────────┘
                            │ HTTP / JSON
┌───────────────────────────▼────────────────────────────┐
│                    Flask Application                   │
│   ┌────────────────────────────────────────────────┐   │
│   │               Route Blueprints                 │   │
│   │   Auth, Dashboard, Products, Suppliers,        │   │
│   │   Inventory, POS, Reports, Users               │   │
│   └───────────────────────▲────────────────────────┘   │
│                           │ Calls                      │
│   ┌───────────────────────▼────────────────────────┐   │
│   │                 Service Layer                  │   │
│   │   auth_service, product_service, pos_service,  │   │
│   │   inventory_service, analytics_service,        │   │
│   │   report_service, supplier_service             │   │
│   └───────────────────────▲────────────────────────┘   │
│                           │ Parametric Queries         │
│   ┌───────────────────────▼────────────────────────┐   │
│   │             Database Access Layer              │   │
│   │    SQLite (PRAGMA foreign_keys = ON, ACIDs)    │   │
│   └────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

## 2. Layered Component Responsibilities

### 2.1 Route Handlers (Blueprints)
- Route handlers strictly handle HTTP requests, session validation, input extraction, and response formatting (HTML render or JSON).
- No business logic or SQL queries exist directly in route controllers.

### 2.2 Service Layer
- **`auth_service.py`**: User authentication, password hashing (`Werkzeug`), session management, and RBAC enforcement decorators (`@login_required`, `@role_required`).
- **`product_service.py`**: Product catalog CRUD, unique SKU validation, stock status calculation (In stock, Low stock, Out of stock, Expiring soon, Expired), and catalog search.
- **`supplier_service.py`**: Vendor management and linked product portfolio tracking.
- **`pos_service.py`**: **Authoritative backend pricing**, atomic transactions, cart validation, discount and tax calculation, payment change calculation, stock deduction, and invoice generation.
- **`inventory_service.py`**: Real-time stock tracking, atomic adjustments, negative stock prevention, stock movement audit trails, reorder formulas, and expiry tracking.
- **`analytics_service.py`**: Business intelligence KPI aggregations and Plotly interactive chart generation.
- **`report_service.py`**: Financial and operational report generation (Daily, Monthly, Product Profitability with COGS/Margins, Low Stock Reorder, Expiry Watch, Full Sales Ledger) and RFC4180 CSV streaming.

### 2.3 Database Layer
- **`app/database.py`**: Connection lifecycle management via Flask's request context `g`, connection pooling helpers, and transactional context managers.
- Enforces relational foreign keys, column CHECK constraints (e.g. `cost_price >= 0`, `quantity >= 0`), and composite performance indexes.

## 3. Security Principles

1. **Backend Price Verification**: The frontend only transmits `{product_id, quantity}`. Client-side price tampering is completely ignored; database prices are always authoritative.
2. **Atomic Inventory Commit**: In `process_sale()`, deducting product quantities, inserting `sales`, `sale_items`, and writing audit `stock_movements` execute in a single ACID transaction. Any failure (e.g., insufficient stock or payment mismatch) triggers an immediate database rollback.
3. **Role-Based Access Control (RBAC)**: Cashiers are strictly prevented from accessing user management, supplier editing, manual inventory adjustments, analytics dashboards, and sensitive administrative financial reports.
4. **SQL Injection Defense**: 100% of queries use parameterization (`?` placeholders). No string concatenation is used in query building.

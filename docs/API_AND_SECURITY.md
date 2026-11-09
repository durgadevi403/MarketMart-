# MarketMate API Specification & Security Architecture

## 1. POS Checkout API

### Endpoint: `POST /pos/checkout`
Processes an in-store transaction with strict backend price validation and atomic inventory deduction.

- **Content-Type**: `application/json`
- **Authentication**: Required (`session['user_id']`)
- **Roles**: `ADMIN`, `CASHIER`

#### Request Payload
```json
{
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 4, "quantity": 1 }
  ],
  "customer_name": "Eleanor Vance",
  "customer_phone": "+1 (555) 301-4491",
  "discount_type": "PERCENTAGE",
  "discount_value": 10.0,
  "payment_method": "CASH",
  "amount_tendered": 50.00,
  "notes": "Customer requested paper bag"
}
```

> **Security Rule**: The request MUST NOT submit prices. Even if a client injects `unit_price`, `selling_price`, or `total` in the JSON body, the backend explicitly ignores it and looks up the authoritative `selling_price` from the SQLite database.

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "invoice_no": "INV-20261102-A1B2",
  "invoice_url": "/pos/invoice/INV-20261102-A1B2",
  "sale": {
    "sale_id": 56,
    "subtotal": 9.47,
    "discount_amount": 0.95,
    "tax_amount": 0.43,
    "final_total": 8.95,
    "amount_tendered": 50.00,
    "change_returned": 41.05
  }
}
```

#### Error Response (`400 Bad Request`)
```json
{
  "success": false,
  "error": "Insufficient stock for 'Hass Avocados (4-Pack)'. Requested: 15, Available in stock: 12."
}
```

---

## 2. Product Search API

### Endpoint: `GET /products/api/search?q={query}&category={category}`
Powers live autocomplete search and barcode scanning inside the POS checkout terminal.

- **Authentication**: Required
- **Returns**: JSON array of matching active catalog items with current stock counts and badges.

---

## 3. Reports & CSV Export APIs

All report routes support streaming RFC4180 CSV files via the query parameter `?export=csv`:

| Endpoint | Export File | Description |
|---|---|---|
| `GET /reports/daily-sales?export=csv` | `daily_sales_report.csv` | Daily financial performance |
| `GET /reports/monthly-sales?export=csv` | `monthly_sales_report.csv` | Monthly historical turnover & AOV |
| `GET /reports/profitability?export=csv` | `product_profitability_report.csv` | COGS, revenue, gross profit & margins |
| `GET /reports/low-stock?export=csv` | `low_stock_reorder_report.csv` | Procurement replenishment schedule |
| `GET /reports/expiry?export=csv` | `expiry_monitoring_report.csv` | Perishable spillage risk ledger |
| `GET /reports/sales-history?export=csv` | `sales_history_report.csv` | Complete transactions ledger |

---

## 4. Threat Matrix & Defensive Countermeasures

| Threat Vector | Severity | Attack Scenario | Countermeasure Implemented |
|---|---|---|---|
| **Price Tampering** | Critical | Client alters JSON payload to buy \$20 items for \$0.01 | Backend recalculates every line item strictly using database `products.selling_price`. Client-submitted prices are discarded. |
| **Negative Inventory Race** | High | Concurrent checkouts oversell remaining stock | Atomic SQLite transactions with immediate checks; raises `ValueError` and rolls back if `quantity < requested`. |
| **SQL Injection** | Critical | Attacker inputs `' OR '1'='1` in product/supplier search | 100% parameterization (`?` placeholders) in all query builders. |
| **Privilege Escalation** | High | Cashier attempts to delete products or view margins | Declarative RBAC decorators (`@role_required(['ADMIN'])`) enforcing HTTP 403 Forbidden on restricted endpoints. |
| **Password Compromise** | High | Database dump exposes plaintext staff passwords | PBKDF2/SHA256 password hashing via Werkzeug with cryptographic salting. |

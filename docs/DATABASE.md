# MarketMate Database Design & Schema Reference

MarketMate uses SQLite with strict relational enforcement (`PRAGMA foreign_keys = ON;`) to guarantee consistency across inventory, sales, suppliers, and audit logs.

## 1. Entity-Relationship Diagram

```
       ┌──────────────────┐
       │      USERS       │
       ├──────────────────┤
       │ id (PK)          │
       │ username         │
       │ password_hash    │
       │ role             │
       └────────┬─────────┘
                │
                │ 1:N
        ┌───────┴────────┐                   ┌──────────────────┐
        │     SALES      │                   │    SUPPLIERS     │
        ├────────────────┤                   ├──────────────────┤
        │ id (PK)        │                   │ id (PK)          │
        │ invoice_no     │                   │ name             │
        │ cashier_id(FK) ├──────────────┐    │ contact_person   │
        │ final_total    │              │    └────────┬─────────┘
        └───────┬────────┘              │             │
                │ 1:N                   │             │ 1:N
        ┌───────┴────────┐              │    ┌────────┴─────────┐
        │   SALE_ITEMS   │              │    │     PRODUCTS     │
        ├────────────────┤              │    ├──────────────────┤
        │ id (PK)        │              │    │ id (PK)          │
        │ sale_id (FK)   │              │    │ sku (UNIQUE)     │
        │ product_id(FK) ├──────────────┼───►│ supplier_id (FK) │
        │ cost_price     │              │    │ cost_price       │
        │ unit_price     │              │    │ selling_price    │
        │ quantity       │              │    │ quantity         │
        └────────────────┘              │    └────────┬─────────┘
                                        │             │ 1:N
                                        │    ┌────────┴─────────┐
                                        │    │ STOCK_MOVEMENTS  │
                                        │    ├──────────────────┤
                                        │    │ id (PK)          │
                                        └────┼──► product_id(FK)│
                                             │ user_id (FK)     │
                                             │ movement_type    │
                                             │ quantity_change  │
                                             └──────────────────┘
```

## 2. Table Specifications

### 2.1 `users`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique user identifier |
| `username` | TEXT | UNIQUE, NOT NULL | Login handle (min. 3 chars) |
| `password_hash` | TEXT | NOT NULL | Werkzeug-generated password hash |
| `full_name` | TEXT | NOT NULL | Staff member display name |
| `email` | TEXT | UNIQUE, NOT NULL | Contact email address |
| `role` | TEXT | CHECK(role IN ('ADMIN', 'CASHIER')) | System access tier |
| `is_active` | INTEGER | DEFAULT 1 CHECK(is_active IN (0,1)) | Status toggle |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Registration timestamp |

### 2.2 `suppliers`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Supplier identifier |
| `name` | TEXT | NOT NULL | Company name |
| `contact_person` | TEXT | NULLABLE | Primary representative |
| `phone` | TEXT | NULLABLE | Contact telephone |
| `email` | TEXT | NULLABLE | Contact email |
| `address` | TEXT | NULLABLE | Physical delivery address |
| `notes` | TEXT | NULLABLE | Ordering terms and logistics notes |

### 2.3 `products`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal product identifier |
| `name` | TEXT | NOT NULL | Grocery product title |
| `sku` | TEXT | UNIQUE, NOT NULL | Universal barcode / SKU code |
| `category` | TEXT | NOT NULL | Grocery category |
| `description` | TEXT | NULLABLE | Specifications / pack size |
| `cost_price` | REAL | NOT NULL CHECK(cost_price >= 0) | Wholesale procurement cost |
| `selling_price`| REAL | NOT NULL CHECK(selling_price >= 0) | Retail consumer price |
| `quantity` | INTEGER | NOT NULL DEFAULT 0 CHECK(quantity >= 0) | Current units on shelf |
| `min_stock_level` | INTEGER | DEFAULT 5 CHECK(min_stock_level >= 0) | Reorder threshold |
| `expiry_date` | DATE | NULLABLE | Perishable expiry date |
| `supplier_id` | INTEGER | FOREIGN KEY -> suppliers(id) | Linked vendor |

### 2.4 `sales`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Sale record ID |
| `invoice_no` | TEXT | UNIQUE, NOT NULL | Formatted identifier (INV-YYYYMMDD-XXXX) |
| `cashier_id` | INTEGER | NOT NULL, FOREIGN KEY -> users(id) | Attributed cashier |
| `customer_name` | TEXT | DEFAULT 'Walk-in Customer' | Customer display name |
| `customer_phone`| TEXT | NULLABLE | Customer phone number |
| `subtotal` | REAL | NOT NULL CHECK(subtotal >= 0) | Gross item sum |
| `discount_type` | TEXT | CHECK IN ('NONE', 'PERCENTAGE', 'FIXED') | Discount applied |
| `discount_amount`| REAL | NOT NULL DEFAULT 0.0 | Dollar value deducted |
| `tax_rate` | REAL | DEFAULT 5.0 | Sales tax percentage |
| `tax_amount` | REAL | NOT NULL DEFAULT 0.0 | Dollar value of tax |
| `final_total` | REAL | NOT NULL CHECK(final_total >= 0) | Net payable amount |
| `payment_method`| TEXT | CHECK IN ('CASH', 'CARD', 'UPI') | Payment medium |
| `amount_tendered`| REAL | DEFAULT 0.0 | Cash given by customer |
| `change_returned`| REAL | DEFAULT 0.0 | Cash returned to customer |

### 2.5 `sale_items`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Item row identifier |
| `sale_id` | INTEGER | FOREIGN KEY -> sales(id) ON DELETE CASCADE | Parent invoice |
| `product_id` | INTEGER | FOREIGN KEY -> products(id) | Source product |
| `product_name` | TEXT | NOT NULL | Historical snapshot of name |
| `product_sku` | TEXT | NOT NULL | Historical snapshot of SKU |
| `cost_price` | REAL | NOT NULL | **Snapshot of cost for accurate COGS/margins** |
| `unit_price` | REAL | NOT NULL | **Authoritative price charged** |
| `quantity` | INTEGER | NOT NULL CHECK(quantity > 0) | Units sold |
| `line_total` | REAL | NOT NULL CHECK(line_total >= 0) | unit_price * quantity |

### 2.6 `stock_movements`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Audit movement identifier |
| `product_id` | INTEGER | FOREIGN KEY -> products(id) ON DELETE CASCADE | Product adjusted |
| `movement_type`| TEXT | CHECK IN ('INITIAL', 'SALE', 'PURCHASE_RECEIPT', 'STOCK_ADJUSTMENT', 'DAMAGE', 'EXPIRY', 'RETURN') | Type of inventory event |
| `quantity_change`| INTEGER | NOT NULL | Signed integer (+ or -) |
| `previous_quantity` | INTEGER | NOT NULL CHECK(previous_quantity >= 0) | Stock before event |
| `new_quantity` | INTEGER | NOT NULL CHECK(new_quantity >= 0) | Stock after event |
| `reference_id` | TEXT | NULLABLE | Invoice # or PO # |
| `reason` | TEXT | NULLABLE | Audit rationale |
| `user_id` | INTEGER | FOREIGN KEY -> users(id) ON DELETE SET NULL | Staff responsible |

## 3. Database Indexes
- `idx_products_sku`: Fast scanning in POS and inventory.
- `idx_products_category`: Categorical grouping and charts.
- `idx_sales_invoice`: Unique instant lookup for receipt display.
- `idx_sales_created`: Fast date-range filtering for financial reports and BI charts.
- `idx_sale_items_sale`: Fast join for itemized receipts.
- `idx_stock_movements_product`: Fast audit trail retrieval by item.

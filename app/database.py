import sqlite3
import os
from contextlib import contextmanager
from flask import g, current_app

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('ADMIN', 'CASHIER')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sku TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    cost_price REAL NOT NULL CHECK(cost_price >= 0),
    selling_price REAL NOT NULL CHECK(selling_price >= 0),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
    min_stock_level INTEGER NOT NULL DEFAULT 5 CHECK(min_stock_level >= 0),
    expiry_date DATE,
    supplier_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);

-- Sales / Invoices table
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT UNIQUE NOT NULL,
    cashier_id INTEGER NOT NULL,
    customer_name TEXT DEFAULT 'Walk-in Customer',
    customer_phone TEXT,
    subtotal REAL NOT NULL CHECK(subtotal >= 0),
    discount_type TEXT CHECK(discount_type IN ('NONE', 'PERCENTAGE', 'FIXED')) DEFAULT 'NONE',
    discount_value REAL NOT NULL DEFAULT 0.0 CHECK(discount_value >= 0),
    discount_amount REAL NOT NULL DEFAULT 0.0 CHECK(discount_amount >= 0),
    tax_rate REAL NOT NULL DEFAULT 5.0 CHECK(tax_rate >= 0),
    tax_amount REAL NOT NULL DEFAULT 0.0 CHECK(tax_amount >= 0),
    final_total REAL NOT NULL CHECK(final_total >= 0),
    payment_method TEXT NOT NULL CHECK(payment_method IN ('CASH', 'CARD', 'UPI')),
    amount_tendered REAL DEFAULT 0.0,
    change_returned REAL DEFAULT 0.0,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cashier_id) REFERENCES users(id)
);

-- Sale line items table
CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    product_sku TEXT NOT NULL,
    cost_price REAL NOT NULL CHECK(cost_price >= 0),
    unit_price REAL NOT NULL CHECK(unit_price >= 0),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    line_total REAL NOT NULL CHECK(line_total >= 0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Stock movements audit table
CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    movement_type TEXT NOT NULL CHECK(movement_type IN ('INITIAL', 'SALE', 'PURCHASE_RECEIPT', 'STOCK_ADJUSTMENT', 'DAMAGE', 'EXPIRY', 'RETURN')),
    quantity_change INTEGER NOT NULL,
    previous_quantity INTEGER NOT NULL CHECK(previous_quantity >= 0),
    new_quantity INTEGER NOT NULL CHECK(new_quantity >= 0),
    reference_id TEXT,
    reason TEXT,
    user_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Application settings table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Performance and constraint indexes
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_sales_invoice ON sales(invoice_no);
CREATE INDEX IF NOT EXISTS idx_sales_created ON sales(created_at);
CREATE INDEX IF NOT EXISTS idx_sales_cashier ON sales(cashier_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_created ON stock_movements(created_at);
"""

def connect_db(db_path):
    """Create a raw database connection with sqlite3.Row and PRAGMA foreign_keys=ON."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_db():
    """Retrieve connection for the current Flask request context."""
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = connect_db(db_path)
    return g.db

def close_db(e=None):
    """Close connection at the end of the Flask request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(db_path=None):
    """Initialize database schema."""
    if db_path is None:
        if current_app:
            db_path = current_app.config['DATABASE_PATH']
        else:
            from config import Config
            db_path = Config.DATABASE_PATH

    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = connect_db(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()

@contextmanager
def transaction(db=None):
    """Context manager for atomic database transactions with rollback on exception."""
    if db is None:
        db = get_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

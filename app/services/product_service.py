from datetime import datetime, date
from app.database import get_db

def compute_stock_status(quantity: int, min_stock: int, expiry_date: str = None) -> dict:
    """Helper to return human-friendly stock status metadata and badge colors."""
    status = 'in_stock'
    label = 'In Stock'
    badge_class = 'badge-soft-success'

    # Check expiry first
    is_expired = False
    is_expiring = False
    if expiry_date:
        try:
            exp = datetime.strptime(expiry_date[:10], '%Y-%m-%d').date()
            today = date.today()
            days_until = (exp - today).days
            if days_until < 0:
                is_expired = True
            elif days_until <= 30:
                is_expiring = True
        except Exception:
            pass

    if quantity == 0:
        status = 'out_of_stock'
        label = 'Out of Stock'
        badge_class = 'badge-soft-danger'
    elif quantity <= min_stock:
        status = 'low_stock'
        label = 'Low Stock'
        badge_class = 'badge-soft-warning'
    
    if is_expired:
        status = 'expired'
        label = 'Expired'
        badge_class = 'badge-soft-danger'
    elif is_expiring and status != 'low_stock':
        status = 'expiring_soon'
        label = 'Expiring Soon'
        badge_class = 'badge-soft-terracotta'

    return {
        'status': status,
        'label': label,
        'badge_class': badge_class,
        'is_expired': is_expired,
        'is_expiring': is_expiring
    }

def get_all_products(search=None, category=None, supplier_id=None, stock_status=None, sort_by='name', order='asc'):
    db = get_db()
    cursor = db.cursor()

    query = """
        SELECT p.*, s.name AS supplier_name
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE 1=1
    """
    params = []

    if search:
        search_pattern = f"%{search.strip()}%"
        query += " AND (p.name LIKE ? OR p.sku LIKE ? OR p.category LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern])

    if category and category != 'All':
        query += " AND p.category = ?"
        params.append(category)

    if supplier_id and supplier_id != 'All':
        query += " AND p.supplier_id = ?"
        params.append(int(supplier_id))

    if stock_status:
        if stock_status == 'out_of_stock':
            query += " AND p.quantity = 0"
        elif stock_status == 'low_stock':
            query += " AND p.quantity > 0 AND p.quantity <= p.min_stock_level"
        elif stock_status == 'in_stock':
            query += " AND p.quantity > p.min_stock_level"
        elif stock_status == 'expired':
            query += " AND p.expiry_date IS NOT NULL AND date(p.expiry_date) < date('now')"
        elif stock_status == 'expiring_soon':
            query += " AND p.expiry_date IS NOT NULL AND date(p.expiry_date) >= date('now') AND date(p.expiry_date) <= date('now', '+30 days')"

    # Sorting whitelist
    valid_sort_columns = {
        'name': 'p.name',
        'sku': 'p.sku',
        'category': 'p.category',
        'selling_price': 'p.selling_price',
        'quantity': 'p.quantity',
        'created_at': 'p.created_at',
        'expiry_date': 'p.expiry_date'
    }
    col = valid_sort_columns.get(sort_by, 'p.name')
    direction = 'DESC' if str(order).lower() == 'desc' else 'ASC'
    query += f" ORDER BY {col} {direction}"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    products = []
    for row in rows:
        p = dict(row)
        p.update(compute_stock_status(p['quantity'], p['min_stock_level'], p.get('expiry_date')))
        products.append(p)
    return products

def get_product_by_id(product_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, s.name AS supplier_name, s.contact_person AS supplier_contact, s.phone AS supplier_phone
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.id = ?
    """, (product_id,))
    row = cursor.fetchone()
    if not row:
        return None
    p = dict(row)
    p.update(compute_stock_status(p['quantity'], p['min_stock_level'], p.get('expiry_date')))
    return p

def get_product_by_sku(sku: str):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, s.name AS supplier_name
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.sku = ?
    """, (sku.strip().upper(),))
    row = cursor.fetchone()
    if not row:
        return None
    p = dict(row)
    p.update(compute_stock_status(p['quantity'], p['min_stock_level'], p.get('expiry_date')))
    return p

def get_categories():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND category != '' ORDER BY category ASC")
    return [row['category'] for row in cursor.fetchall()]

def create_product(name: str, sku: str, category: str, description: str,
                   cost_price: float, selling_price: float, quantity: int,
                   min_stock_level: int, expiry_date: str = None, supplier_id: int = None,
                   user_id: int = None):
    name = (name or '').strip()
    sku = (sku or '').strip().upper()
    category = (category or '').strip()

    if not name:
        raise ValueError("Product name is required.")
    if not sku:
        raise ValueError("Product SKU is required.")
    if not category:
        raise ValueError("Category is required.")

    try:
        cost_price = float(cost_price)
        selling_price = float(selling_price)
        quantity = int(quantity)
        min_stock_level = int(min_stock_level)
    except (ValueError, TypeError):
        raise ValueError("Prices and quantities must be valid numbers.")

    if cost_price < 0:
        raise ValueError("Cost price cannot be negative.")
    if selling_price < 0:
        raise ValueError("Selling price cannot be negative.")
    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")
    if min_stock_level < 0:
        raise ValueError("Minimum stock level cannot be negative.")

    cleaned_expiry = expiry_date.strip() if expiry_date and expiry_date.strip() else None
    cleaned_supplier = int(supplier_id) if supplier_id and str(supplier_id).isdigit() and int(supplier_id) > 0 else None

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO products (name, sku, category, description, cost_price, selling_price, quantity, min_stock_level, expiry_date, supplier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, sku, category, description.strip() if description else None,
              cost_price, selling_price, quantity, min_stock_level, cleaned_expiry, cleaned_supplier))
        
        product_id = cursor.lastrowid

        # Record initial stock movement
        if quantity > 0:
            cursor.execute("""
                INSERT INTO stock_movements (product_id, movement_type, quantity_change, previous_quantity, new_quantity, reference_id, reason, user_id)
                VALUES (?, 'INITIAL', ?, 0, ?, 'INITIAL-STOCK', 'Initial inventory batch', ?)
            """, (product_id, quantity, quantity, user_id))

        db.commit()
        return product_id
    except Exception as e:
        db.rollback()
        if 'UNIQUE constraint failed: products.sku' in str(e):
            raise ValueError(f"SKU '{sku}' already exists. Please choose a unique SKU.")
        raise

def update_product(product_id: int, name: str, sku: str, category: str, description: str,
                   cost_price: float, selling_price: float, min_stock_level: int,
                   expiry_date: str = None, supplier_id: int = None):
    name = (name or '').strip()
    sku = (sku or '').strip().upper()
    category = (category or '').strip()

    if not name:
        raise ValueError("Product name is required.")
    if not sku:
        raise ValueError("Product SKU is required.")
    if not category:
        raise ValueError("Category is required.")

    try:
        cost_price = float(cost_price)
        selling_price = float(selling_price)
        min_stock_level = int(min_stock_level)
    except (ValueError, TypeError):
        raise ValueError("Prices and stock levels must be valid numbers.")

    if cost_price < 0:
        raise ValueError("Cost price cannot be negative.")
    if selling_price < 0:
        raise ValueError("Selling price cannot be negative.")
    if min_stock_level < 0:
        raise ValueError("Minimum stock level cannot be negative.")

    cleaned_expiry = expiry_date.strip() if expiry_date and expiry_date.strip() else None
    cleaned_supplier = int(supplier_id) if supplier_id and str(supplier_id).isdigit() and int(supplier_id) > 0 else None

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE products
            SET name = ?, sku = ?, category = ?, description = ?, cost_price = ?, selling_price = ?,
                min_stock_level = ?, expiry_date = ?, supplier_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (name, sku, category, description.strip() if description else None,
              cost_price, selling_price, min_stock_level, cleaned_expiry, cleaned_supplier, product_id))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        if 'UNIQUE constraint failed: products.sku' in str(e):
            raise ValueError(f"SKU '{sku}' is already in use by another product.")
        raise

def delete_product(product_id: int):
    db = get_db()
    cursor = db.cursor()
    # Check if there are sales recorded for this product
    cursor.execute("SELECT COUNT(*) AS count FROM sale_items WHERE product_id = ?", (product_id,))
    sales_count = cursor.fetchone()['count']
    if sales_count > 0:
        raise ValueError("This product cannot be deleted because it is linked to historical sales records. To retire it, adjust its quantity to 0.")

    try:
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise

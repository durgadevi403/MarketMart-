from datetime import datetime, date
from app.database import get_db

def adjust_stock(product_id: int, quantity_change: int, movement_type: str,
                 reason: str = None, reference_id: str = None, user_id: int = None):
    """
    Adjust product stock atomically, verifying that stock never drops below 0,
    and recording an audit trail in stock_movements.
    """
    valid_types = ('PURCHASE_RECEIPT', 'STOCK_ADJUSTMENT', 'DAMAGE', 'EXPIRY', 'RETURN')
    movement_type = (movement_type or '').strip().upper()
    if movement_type not in valid_types:
        raise ValueError(f"Invalid movement type '{movement_type}'. Must be one of: {', '.join(valid_types)}")

    try:
        quantity_change = int(quantity_change)
    except (ValueError, TypeError):
        raise ValueError("Quantity change must be an integer.")

    if quantity_change == 0:
        raise ValueError("Quantity change cannot be zero.")

    db = get_db()
    cursor = db.cursor()

    # Lock & read current product
    cursor.execute("SELECT id, name, quantity FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        raise ValueError("Product not found.")

    current_qty = product['quantity']
    new_qty = current_qty + quantity_change

    if new_qty < 0:
        raise ValueError(f"Insufficient stock for {product['name']}. Current stock is {current_qty}, cannot reduce by {abs(quantity_change)}.")

    try:
        # Update product quantity
        cursor.execute("""
            UPDATE products
            SET quantity = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_qty, product_id))

        # Insert movement record
        cursor.execute("""
            INSERT INTO stock_movements (product_id, movement_type, quantity_change, previous_quantity, new_quantity, reference_id, reason, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, movement_type, quantity_change, current_qty, new_qty,
              reference_id or f"ADJ-{datetime.now().strftime('%Y%m%d%H%M%S')}",
              reason or f"Manual stock adjustment ({movement_type})", user_id))

        db.commit()
        return {
            'product_id': product_id,
            'previous_quantity': current_qty,
            'new_quantity': new_qty,
            'quantity_change': quantity_change
        }
    except Exception:
        db.rollback()
        raise

def get_stock_movements(product_id=None, movement_type=None, limit=100):
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT sm.*, p.name AS product_name, p.sku AS product_sku, p.category, u.username AS user_name
        FROM stock_movements sm
        JOIN products p ON sm.product_id = p.id
        LEFT JOIN users u ON sm.user_id = u.id
        WHERE 1=1
    """
    params = []
    if product_id:
        query += " AND sm.product_id = ?"
        params.append(product_id)
    if movement_type and movement_type != 'All':
        query += " AND sm.movement_type = ?"
        params.append(movement_type)

    query += " ORDER BY sm.created_at DESC, sm.id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

def get_low_stock_items():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, s.name AS supplier_name, s.contact_person, s.phone AS supplier_phone, s.email AS supplier_email
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.quantity <= p.min_stock_level
        ORDER BY p.quantity ASC, p.name ASC
    """)
    items = []
    for row in cursor.fetchall():
        item = dict(row)
        # Compute recommended reorder quantity
        reorder_qty = max((item['min_stock_level'] * 2) - item['quantity'], 10)
        est_cost = round(reorder_qty * item['cost_price'], 2)
        item['recommended_reorder'] = reorder_qty
        item['estimated_reorder_cost'] = est_cost
        items.append(item)
    return items

def get_expiry_alerts():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT p.*, s.name AS supplier_name,
               CAST((julianday(p.expiry_date) - julianday('now')) AS INTEGER) AS days_until_expiry
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.expiry_date IS NOT NULL AND date(p.expiry_date) <= date('now', '+30 days')
        ORDER BY p.expiry_date ASC
    """)
    alerts = []
    for row in cursor.fetchall():
        item = dict(row)
        days = item.get('days_until_expiry', 0)
        if days < 0:
            item['expiry_status'] = 'EXPIRED'
            item['expiry_label'] = f"Expired {abs(days)} day{'s' if abs(days) != 1 else ''} ago"
            item['badge_class'] = 'badge-soft-danger'
        elif days == 0:
            item['expiry_status'] = 'EXPIRES_TODAY'
            item['expiry_label'] = 'Expires today'
            item['badge_class'] = 'badge-soft-danger'
        else:
            item['expiry_status'] = 'EXPIRING_SOON'
            item['expiry_label'] = f"Expires in {days} day{'s' if days != 1 else ''}"
            item['badge_class'] = 'badge-soft-warning'
        alerts.append(item)
    return alerts

def get_inventory_summary():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) AS total_skus,
            COALESCE(SUM(quantity), 0) AS total_units,
            COALESCE(SUM(quantity * cost_price), 0) AS total_cost_valuation,
            COALESCE(SUM(quantity * selling_price), 0) AS total_retail_valuation,
            SUM(CASE WHEN quantity <= min_stock_level THEN 1 ELSE 0 END) AS low_stock_count,
            SUM(CASE WHEN quantity = 0 THEN 1 ELSE 0 END) AS out_of_stock_count,
            SUM(CASE WHEN expiry_date IS NOT NULL AND date(expiry_date) <= date('now', '+30 days') THEN 1 ELSE 0 END) AS expiring_count
        FROM products
    """)
    row = cursor.fetchone()
    return dict(row) if row else {}

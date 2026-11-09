import uuid
from datetime import datetime
from flask import current_app
from app.database import get_db

def generate_invoice_number() -> str:
    """Generate clean, unique, sequential-formatted invoice identifier."""
    now = datetime.now()
    timestamp_prefix = now.strftime('%Y%m%d%H%M')
    short_uuid = uuid.uuid4().hex[:4].upper()
    return f"INV-{timestamp_prefix}-{short_uuid}"

def calculate_totals(items_with_db_prices, discount_type='NONE', discount_value=0.0, tax_rate=5.0):
    """
    Pure calculation helper using DB prices only.
    """
    subtotal = sum(item['unit_price'] * item['quantity'] for item in items_with_db_prices)
    subtotal = round(subtotal, 2)

    discount_type = (discount_type or 'NONE').upper()
    try:
        discount_value = float(discount_value or 0.0)
    except (ValueError, TypeError):
        discount_value = 0.0

    if discount_value < 0:
        raise ValueError("Discount value cannot be negative.")

    discount_amount = 0.0
    if discount_type == 'PERCENTAGE':
        if discount_value > 100.0:
            raise ValueError("Percentage discount cannot exceed 100%.")
        discount_amount = round(subtotal * (discount_value / 100.0), 2)
    elif discount_type == 'FIXED':
        if discount_value > subtotal:
            raise ValueError(f"Fixed discount (${discount_value:.2f}) cannot exceed subtotal (${subtotal:.2f}).")
        discount_amount = round(discount_value, 2)
    else:
        discount_type = 'NONE'
        discount_value = 0.0
        discount_amount = 0.0

    taxable_amount = max(0.0, round(subtotal - discount_amount, 2))
    tax_rate = float(tax_rate if tax_rate is not None else 5.0)
    if tax_rate < 0:
        tax_rate = 0.0
    tax_amount = round(taxable_amount * (tax_rate / 100.0), 2)
    final_total = round(taxable_amount + tax_amount, 2)

    return {
        'subtotal': subtotal,
        'discount_type': discount_type,
        'discount_value': discount_value,
        'discount_amount': discount_amount,
        'tax_rate': tax_rate,
        'tax_amount': tax_amount,
        'final_total': final_total
    }

def process_sale(cart_items: list, cashier_id: int, customer_name: str = 'Walk-in Customer',
                 customer_phone: str = None, discount_type: str = 'NONE', discount_value: float = 0.0,
                 payment_method: str = 'CASH', amount_tendered: float = 0.0, notes: str = None,
                 tax_rate: float = None):
    """
    Atomically processes a sale:
    1. Validates cart.
    2. Fetches authoritative prices and checks stock from DB.
    3. Calculates subtotal, discount, tax, final total.
    4. Validates payment amount and change.
    5. Deducts stock and writes sales, sale_items, stock_movements.
    6. Commits or rolls back on any error.
    """
    if not cart_items or not isinstance(cart_items, list):
        raise ValueError("Shopping cart cannot be empty.")

    payment_method = (payment_method or '').strip().upper()
    if payment_method not in ('CASH', 'CARD', 'UPI'):
        raise ValueError("Payment method must be one of: CASH, CARD, UPI.")

    if tax_rate is None:
        try:
            tax_rate = float(current_app.config.get('DEFAULT_TAX_RATE', 5.0))
        except Exception:
            tax_rate = 5.0

    # Consolidate duplicate products if sent in list
    consolidated = {}
    for item in cart_items:
        try:
            p_id = int(item['product_id'])
            qty = int(item['quantity'])
        except (KeyError, ValueError, TypeError):
            raise ValueError("Each cart item must specify a valid integer product_id and quantity.")

        if qty <= 0:
            raise ValueError("Item quantity must be greater than zero.")
        consolidated[p_id] = consolidated.get(p_id, 0) + qty

    db = get_db()
    cursor = db.cursor()

    # Step 1: Verify all products and fetch official DB prices
    verified_items = []
    for product_id, req_qty in consolidated.items():
        cursor.execute("""
            SELECT id, name, sku, cost_price, selling_price, quantity
            FROM products WHERE id = ?
        """, (product_id,))
        prod = cursor.fetchone()
        if not prod:
            raise ValueError(f"Product ID {product_id} was not found in catalog.")

        current_qty = prod['quantity']
        if req_qty > current_qty:
            raise ValueError(
                f"Insufficient stock for '{prod['name']}' (SKU: {prod['sku']}). "
                f"Requested: {req_qty}, Available in stock: {current_qty}."
            )

        unit_price = float(prod['selling_price'])
        cost_price = float(prod['cost_price'])
        line_total = round(unit_price * req_qty, 2)

        verified_items.append({
            'product_id': prod['id'],
            'product_name': prod['name'],
            'product_sku': prod['sku'],
            'cost_price': cost_price,
            'unit_price': unit_price,
            'quantity': req_qty,
            'line_total': line_total,
            'current_stock': current_qty,
            'new_stock': current_qty - req_qty
        })

    # Step 2: Compute authoritative totals
    totals = calculate_totals(verified_items, discount_type, discount_value, tax_rate)
    final_total = totals['final_total']

    # Step 3: Payment validation
    try:
        tendered = float(amount_tendered or 0.0)
    except (ValueError, TypeError):
        tendered = 0.0

    if payment_method == 'CASH':
        if tendered < final_total:
            raise ValueError(
                f"Cash tendered (${tendered:,.2f}) is less than total payable (${final_total:,.2f})."
            )
        change_returned = round(tendered - final_total, 2)
    else:
        tendered = final_total
        change_returned = 0.0

    # Step 4: Atomic commit across sales, sale_items, products and stock_movements
    invoice_no = generate_invoice_number()
    clean_cust_name = (customer_name or 'Walk-in Customer').strip() or 'Walk-in Customer'
    clean_cust_phone = customer_phone.strip() if customer_phone else None

    try:
        # Insert main sales record
        cursor.execute("""
            INSERT INTO sales (
                invoice_no, cashier_id, customer_name, customer_phone,
                subtotal, discount_type, discount_value, discount_amount,
                tax_rate, tax_amount, final_total, payment_method,
                amount_tendered, change_returned, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_no, cashier_id, clean_cust_name, clean_cust_phone,
            totals['subtotal'], totals['discount_type'], totals['discount_value'],
            totals['discount_amount'], totals['tax_rate'], totals['tax_amount'],
            final_total, payment_method, tendered, change_returned,
            notes.strip() if notes else None
        ))
        sale_id = cursor.lastrowid

        # Insert each line item and update stock
        for item in verified_items:
            cursor.execute("""
                INSERT INTO sale_items (
                    sale_id, product_id, product_name, product_sku,
                    cost_price, unit_price, quantity, line_total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sale_id, item['product_id'], item['product_name'], item['product_sku'],
                item['cost_price'], item['unit_price'], item['quantity'], item['line_total']
            ))

            # Deduct inventory
            cursor.execute("""
                UPDATE products
                SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (item['new_stock'], item['product_id']))

            # Record stock audit movement
            cursor.execute("""
                INSERT INTO stock_movements (
                    product_id, movement_type, quantity_change, previous_quantity,
                    new_quantity, reference_id, reason, user_id
                ) VALUES (?, 'SALE', ?, ?, ?, ?, ?, ?)
            """, (
                item['product_id'], -item['quantity'], item['current_stock'],
                item['new_stock'], invoice_no, f"POS Sale {invoice_no}", cashier_id
            ))

        db.commit()

        return {
            'sale_id': sale_id,
            'invoice_no': invoice_no,
            'created_at': datetime.now().isoformat(),
            'customer_name': clean_cust_name,
            'customer_phone': clean_cust_phone,
            'payment_method': payment_method,
            'subtotal': totals['subtotal'],
            'discount_type': totals['discount_type'],
            'discount_value': totals['discount_value'],
            'discount_amount': totals['discount_amount'],
            'tax_rate': totals['tax_rate'],
            'tax_amount': totals['tax_amount'],
            'final_total': final_total,
            'amount_tendered': tendered,
            'change_returned': change_returned,
            'items': verified_items
        }

    except Exception:
        db.rollback()
        raise

def get_sale_by_invoice(invoice_no: str):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.*, u.full_name AS cashier_name, u.username AS cashier_username
        FROM sales s
        LEFT JOIN users u ON s.cashier_id = u.id
        WHERE s.invoice_no = ?
    """, (invoice_no.strip(),))
    sale = cursor.fetchone()
    if not sale:
        return None
    sale_data = dict(sale)

    cursor.execute("""
        SELECT si.*, p.category
        FROM sale_items si
        LEFT JOIN products p ON si.product_id = p.id
        WHERE si.sale_id = ?
        ORDER BY si.id ASC
    """, (sale_data['id'],))
    sale_data['items'] = [dict(row) for row in cursor.fetchall()]
    return sale_data

def get_sales_history(search=None, start_date=None, end_date=None, cashier_id=None, limit=100):
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT s.*, u.full_name AS cashier_name,
               (SELECT COUNT(*) FROM sale_items WHERE sale_id = s.id) AS item_count
        FROM sales s
        LEFT JOIN users u ON s.cashier_id = u.id
        WHERE 1=1
    """
    params = []

    if search:
        search_pattern = f"%{search.strip()}%"
        query += " AND (s.invoice_no LIKE ? OR s.customer_name LIKE ? OR s.customer_phone LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern])

    if start_date:
        query += " AND date(s.created_at) >= date(?)"
        params.append(start_date)

    if end_date:
        query += " AND date(s.created_at) <= date(?)"
        params.append(end_date)

    if cashier_id:
        query += " AND s.cashier_id = ?"
        params.append(cashier_id)

    query += " ORDER BY s.created_at DESC, s.id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

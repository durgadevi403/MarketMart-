import csv
import io
from datetime import datetime, date
from app.database import get_db

def get_daily_sales_report(start_date=None, end_date=None):
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT
            date(s.created_at) AS sale_date,
            COUNT(s.id) AS transaction_count,
            COALESCE(SUM(s.subtotal), 0) AS gross_sales,
            COALESCE(SUM(s.discount_amount), 0) AS total_discount,
            COALESCE(SUM(s.tax_amount), 0) AS total_tax,
            COALESCE(SUM(s.final_total), 0) AS net_revenue,
            COALESCE(SUM(CASE WHEN s.payment_method = 'CASH' THEN s.final_total ELSE 0 END), 0) AS cash_revenue,
            COALESCE(SUM(CASE WHEN s.payment_method = 'CARD' THEN s.final_total ELSE 0 END), 0) AS card_revenue,
            COALESCE(SUM(CASE WHEN s.payment_method = 'UPI' THEN s.final_total ELSE 0 END), 0) AS upi_revenue
        FROM sales s
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date(s.created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(s.created_at) <= date(?)"
        params.append(end_date)

    query += " GROUP BY date(s.created_at) ORDER BY sale_date DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]

    # Summary totals
    totals = {
        'transaction_count': sum(r['transaction_count'] for r in rows),
        'gross_sales': sum(r['gross_sales'] for r in rows),
        'total_discount': sum(r['total_discount'] for r in rows),
        'total_tax': sum(r['total_tax'] for r in rows),
        'net_revenue': sum(r['net_revenue'] for r in rows),
        'cash_revenue': sum(r['cash_revenue'] for r in rows),
        'card_revenue': sum(r['card_revenue'] for r in rows),
        'upi_revenue': sum(r['upi_revenue'] for r in rows),
    }
    return rows, totals

def get_monthly_sales_report():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT
            strftime('%Y-%m', created_at) AS month_year,
            COUNT(id) AS transaction_count,
            COALESCE(SUM(subtotal), 0) AS gross_sales,
            COALESCE(SUM(discount_amount), 0) AS total_discount,
            COALESCE(SUM(tax_amount), 0) AS total_tax,
            COALESCE(SUM(final_total), 0) AS net_revenue,
            COALESCE(AVG(final_total), 0) AS average_order_value
        FROM sales
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY month_year DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    totals = {
        'transaction_count': sum(r['transaction_count'] for r in rows),
        'gross_sales': sum(r['gross_sales'] for r in rows),
        'total_discount': sum(r['total_discount'] for r in rows),
        'total_tax': sum(r['total_tax'] for r in rows),
        'net_revenue': sum(r['net_revenue'] for r in rows),
        'average_order_value': (sum(r['net_revenue'] for r in rows) / sum(r['transaction_count'] for r in rows)) if rows and sum(r['transaction_count'] for r in rows) > 0 else 0.0
    }
    return rows, totals

def get_profitability_report(start_date=None, end_date=None):
    """
    Computes accurate profitability per product using historical COGS snapshots
    from sale_items.
    """
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT
            si.product_sku,
            si.product_name,
            p.category,
            SUM(si.quantity) AS units_sold,
            SUM(si.line_total) AS total_revenue,
            SUM(si.quantity * si.cost_price) AS total_cogs
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        LEFT JOIN products p ON si.product_id = p.id
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date(s.created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(s.created_at) <= date(?)"
        params.append(end_date)

    query += " GROUP BY si.product_id ORDER BY total_revenue DESC"
    cursor.execute(query, params)
    raw_rows = cursor.fetchall()

    rows = []
    for r in raw_rows:
        item = dict(r)
        revenue = float(item['total_revenue'])
        cogs = float(item['total_cogs'])
        gross_profit = round(revenue - cogs, 2)
        margin_pct = round((gross_profit / revenue * 100), 2) if revenue > 0 else 0.0

        item['gross_profit'] = gross_profit
        item['margin_pct'] = margin_pct
        rows.append(item)

    totals = {
        'units_sold': sum(r['units_sold'] for r in rows),
        'total_revenue': sum(r['total_revenue'] for r in rows),
        'total_cogs': sum(r['total_cogs'] for r in rows),
        'gross_profit': sum(r['gross_profit'] for r in rows),
    }
    totals['margin_pct'] = round((totals['gross_profit'] / totals['total_revenue'] * 100), 2) if totals['total_revenue'] > 0 else 0.0
    return rows, totals

def get_low_stock_report():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT
            p.sku,
            p.name,
            p.category,
            p.quantity AS current_stock,
            p.min_stock_level,
            p.cost_price,
            s.name AS supplier_name,
            s.contact_person,
            s.phone AS supplier_phone,
            s.email AS supplier_email
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.quantity <= p.min_stock_level
        ORDER BY p.quantity ASC, p.name ASC
    """)
    rows = []
    for r in cursor.fetchall():
        item = dict(r)
        deficit = max(0, item['min_stock_level'] - item['current_stock'])
        recommended_reorder = max((item['min_stock_level'] * 2) - item['current_stock'], 10)
        item['deficit'] = deficit
        item['recommended_reorder'] = recommended_reorder
        item['estimated_cost'] = round(recommended_reorder * item['cost_price'], 2)
        rows.append(item)

    totals = {
        'total_low_stock_items': len(rows),
        'total_reorder_units': sum(r['recommended_reorder'] for r in rows),
        'total_estimated_reorder_cost': sum(r['estimated_cost'] for r in rows)
    }
    return rows, totals

def get_expiry_report():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT
            p.sku,
            p.name,
            p.category,
            p.quantity,
            p.selling_price,
            p.expiry_date,
            s.name AS supplier_name,
            CAST((julianday(p.expiry_date) - julianday('now')) AS INTEGER) AS days_remaining
        FROM products p
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.expiry_date IS NOT NULL
        ORDER BY p.expiry_date ASC
    """)
    rows = []
    for r in cursor.fetchall():
        item = dict(r)
        days = item.get('days_remaining', 0)
        item['value_at_risk'] = round(item['quantity'] * item['selling_price'], 2)
        if days < 0:
            item['status'] = 'Expired'
            item['status_badge'] = 'badge-soft-danger'
        elif days <= 30:
            item['status'] = 'Expiring Soon'
            item['status_badge'] = 'badge-soft-warning'
        else:
            item['status'] = 'Valid'
            item['status_badge'] = 'badge-soft-success'
        rows.append(item)

    totals = {
        'total_monitored': len(rows),
        'expired_count': sum(1 for r in rows if r['status'] == 'Expired'),
        'expiring_soon_count': sum(1 for r in rows if r['status'] == 'Expiring Soon'),
        'total_value_at_risk': sum(r['value_at_risk'] for r in rows if r['status'] in ('Expired', 'Expiring Soon'))
    }
    return rows, totals

def get_sales_history_report(start_date=None, end_date=None):
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT
            s.invoice_no,
            s.created_at,
            u.full_name AS cashier_name,
            s.customer_name,
            s.customer_phone,
            (SELECT COUNT(*) FROM sale_items WHERE sale_id = s.id) AS items_count,
            s.subtotal,
            s.discount_amount,
            s.tax_amount,
            s.final_total,
            s.payment_method
        FROM sales s
        LEFT JOIN users u ON s.cashier_id = u.id
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date(s.created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(s.created_at) <= date(?)"
        params.append(end_date)
    query += " ORDER BY s.created_at DESC"

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    totals = {
        'total_invoices': len(rows),
        'total_revenue': sum(r['final_total'] for r in rows),
        'total_tax': sum(r['tax_amount'] for r in rows),
        'total_discount': sum(r['discount_amount'] for r in rows)
    }
    return rows, totals

def generate_csv(headers: list, rows: list) -> str:
    """Helper to convert list of dictionaries or tuples to RFC4180 CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([h[1] for h in headers])

    for row in rows:
        line = []
        for key, _ in headers:
            val = row.get(key, '')
            if isinstance(val, float):
                val = f"{val:.2f}"
            line.append(val)
        writer.writerow(line)

    return output.getvalue()

from flask import Blueprint, render_template, request, Response, session
from app.services.auth_service import login_required, role_required
from app.services.report_service import (
    get_daily_sales_report, get_monthly_sales_report,
    get_profitability_report, get_low_stock_report,
    get_expiry_report, get_sales_history_report, generate_csv
)

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
@role_required(['ADMIN'])
def index():
    return render_template('reports/index.html')

@reports_bp.route('/daily-sales')
@login_required
@role_required(['ADMIN'])
def daily_sales():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    export = request.args.get('export')

    rows, totals = get_daily_sales_report(start_date, end_date)

    if export == 'csv':
        headers = [
            ('sale_date', 'Date'),
            ('transaction_count', 'Transactions'),
            ('gross_sales', 'Gross Sales ($)'),
            ('total_discount', 'Discounts ($)'),
            ('total_tax', 'Tax ($)'),
            ('net_revenue', 'Net Revenue ($)'),
            ('cash_revenue', 'Cash ($)'),
            ('card_revenue', 'Card ($)'),
            ('upi_revenue', 'UPI ($)')
        ]
        csv_data = generate_csv(headers, rows)
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=daily_sales_report.csv'}
        )

    return render_template(
        'reports/daily_sales.html',
        rows=rows,
        totals=totals,
        start_date=start_date,
        end_date=end_date
    )

@reports_bp.route('/monthly-sales')
@login_required
@role_required(['ADMIN'])
def monthly_sales():
    export = request.args.get('export')
    rows, totals = get_monthly_sales_report()

    if export == 'csv':
        headers = [
            ('month_year', 'Month'),
            ('transaction_count', 'Transactions'),
            ('gross_sales', 'Gross Sales ($)'),
            ('total_discount', 'Discounts ($)'),
            ('total_tax', 'Tax ($)'),
            ('net_revenue', 'Net Revenue ($)'),
            ('average_order_value', 'AOV ($)')
        ]
        csv_data = generate_csv(headers, rows)
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=monthly_sales_report.csv'}
        )

    return render_template('reports/monthly_sales.html', rows=rows, totals=totals)

@reports_bp.route('/profitability')
@login_required
@role_required(['ADMIN'])
def profitability():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    export = request.args.get('export')

    rows, totals = get_profitability_report(start_date, end_date)

    if export == 'csv':
        headers = [
            ('product_sku', 'SKU'),
            ('product_name', 'Product Name'),
            ('category', 'Category'),
            ('units_sold', 'Units Sold'),
            ('total_revenue', 'Revenue ($)'),
            ('total_cogs', 'Cost of Goods Sold ($)'),
            ('gross_profit', 'Gross Profit ($)'),
            ('margin_pct', 'Profit Margin (%)')
        ]
        csv_data = generate_csv(headers, rows)
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=product_profitability_report.csv'}
        )

    return render_template(
        'reports/profitability.html',
        rows=rows,
        totals=totals,
        start_date=start_date,
        end_date=end_date
    )

@reports_bp.route('/low-stock')
@login_required
@role_required(['ADMIN'])
def low_stock():
    export = request.args.get('export')
    rows, totals = get_low_stock_report()

    if export == 'csv':
        headers = [
            ('sku', 'SKU'),
            ('name', 'Product Name'),
            ('category', 'Category'),
            ('current_stock', 'Current Stock'),
            ('min_stock_level', 'Min Stock Level'),
            ('deficit', 'Deficit'),
            ('recommended_reorder', 'Recommended Reorder'),
            ('cost_price', 'Cost Price ($)'),
            ('estimated_cost', 'Estimated Reorder Cost ($)'),
            ('supplier_name', 'Supplier'),
            ('supplier_phone', 'Supplier Phone')
        ]
        csv_data = generate_csv(headers, rows)
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=low_stock_reorder_report.csv'}
        )

    return render_template('reports/low_stock.html', rows=rows, totals=totals)

@reports_bp.route('/expiry')
@login_required
@role_required(['ADMIN'])
def expiry():
    export = request.args.get('export')
    rows, totals = get_expiry_report()

    if export == 'csv':
        headers = [
            ('sku', 'SKU'),
            ('name', 'Product Name'),
            ('category', 'Category'),
            ('quantity', 'Current Quantity'),
            ('selling_price', 'Selling Price ($)'),
            ('value_at_risk', 'Value at Risk ($)'),
            ('expiry_date', 'Expiry Date'),
            ('status', 'Status'),
            ('days_remaining', 'Days Remaining'),
            ('supplier_name', 'Supplier')
        ]
        csv_data = generate_csv(headers, rows)
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=expiry_monitoring_report.csv'}
        )

    return render_template('reports/expiry.html', rows=rows, totals=totals)

@reports_bp.route('/sales-history')
@login_required
@role_required(['ADMIN'])
def sales_history():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    export = request.args.get('export')

    rows, totals = get_sales_history_report(start_date, end_date)

    if export == 'csv':
        headers = [
            ('invoice_no', 'Invoice Number'),
            ('created_at', 'Date Time'),
            ('cashier_name', 'Cashier'),
            ('customer_name', 'Customer Name'),
            ('customer_phone', 'Customer Phone'),
            ('items_count', 'Item Count'),
            ('subtotal', 'Subtotal ($)'),
            ('discount_amount', 'Discount ($)'),
            ('tax_amount', 'Tax ($)'),
            ('final_total', 'Final Total ($)'),
            ('payment_method', 'Payment Method')
        ]
        csv_data = generate_csv(headers, rows)
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=sales_history_report.csv'}
        )

    return render_template(
        'reports/sales_history.html',
        rows=rows,
        totals=totals,
        start_date=start_date,
        end_date=end_date
    )

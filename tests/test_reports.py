import pytest
from app.services.report_service import (
    get_daily_sales_report, get_monthly_sales_report,
    get_profitability_report, get_low_stock_report,
    get_expiry_report, get_sales_history_report, generate_csv
)

def test_daily_sales_report_data(app):
    with app.app_context():
        rows, totals = get_daily_sales_report()
        assert len(rows) > 0
        assert totals['transaction_count'] > 0
        assert totals['net_revenue'] > 0

def test_monthly_sales_report_data(app):
    with app.app_context():
        rows, totals = get_monthly_sales_report()
        assert len(rows) > 0
        assert totals['transaction_count'] > 0
        assert totals['average_order_value'] > 0

def test_profitability_report_formulas(app):
    with app.app_context():
        rows, totals = get_profitability_report()
        assert len(rows) > 0
        for r in rows:
            # Formula: gross_profit = round(revenue - cogs, 2)
            expected_profit = round(r['total_revenue'] - r['total_cogs'], 2)
            assert abs(r['gross_profit'] - expected_profit) < 0.05
            # Margin check
            if r['total_revenue'] > 0:
                expected_margin = round((r['gross_profit'] / r['total_revenue']) * 100, 2)
                assert abs(r['margin_pct'] - expected_margin) < 0.1

def test_csv_generator_helper():
    headers = [('id', 'ID'), ('name', 'Name'), ('price', 'Price ($)')]
    rows = [
        {'id': 1, 'name': 'Apples', 'price': 2.50},
        {'id': 2, 'name': 'Bread, Sourdough', 'price': 4.00}
    ]
    csv_str = generate_csv(headers, rows)
    lines = csv_str.strip().splitlines()
    assert lines[0] == "ID,Name,Price ($)"
    assert "1,Apples,2.50" in lines[1]
    assert '"Bread, Sourdough"' in lines[2] # Escaped comma

def test_reports_web_routes_and_csv_exports(admin_client):
    endpoints = [
        ('/reports/daily-sales', 'daily_sales_report.csv'),
        ('/reports/monthly-sales', 'monthly_sales_report.csv'),
        ('/reports/profitability', 'product_profitability_report.csv'),
        ('/reports/low-stock', 'low_stock_reorder_report.csv'),
        ('/reports/expiry', 'expiry_monitoring_report.csv'),
        ('/reports/sales-history', 'sales_history_report.csv')
    ]

    for url, filename in endpoints:
        # Test HTML page view
        html_resp = admin_client.get(url)
        assert html_resp.status_code == 200

        # Test CSV export
        csv_resp = admin_client.get(f"{url}?export=csv")
        assert csv_resp.status_code == 200
        assert csv_resp.headers['Content-Type'].startswith('text/csv')
        assert f"filename={filename}" in csv_resp.headers['Content-Disposition']
        assert len(csv_resp.data) > 20

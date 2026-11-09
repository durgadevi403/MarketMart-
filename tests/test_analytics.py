import json
import pytest
from app.services.analytics_service import (
    get_kpis, get_revenue_trend_chart, get_category_sales_chart,
    get_top_products_chart, get_payment_methods_chart,
    get_monthly_comparison_chart, get_inventory_distribution_chart
)

def test_kpi_calculations(app):
    with app.app_context():
        kpis = get_kpis()
        assert 'total_revenue' in kpis
        assert 'total_transactions' in kpis
        assert 'average_order_value' in kpis
        assert 'total_skus' in kpis
        assert 'low_stock_count' in kpis

        assert kpis['total_transactions'] > 0
        assert kpis['total_revenue'] > 0
        assert kpis['average_order_value'] > 0
        assert kpis['total_skus'] > 0

def test_plotly_chart_generators(app):
    with app.app_context():
        # Revenue trend
        chart_json = get_revenue_trend_chart()
        parsed = json.loads(chart_json)
        assert 'data' in parsed
        assert 'layout' in parsed

        # Category sales
        chart_json = get_category_sales_chart()
        parsed = json.loads(chart_json)
        assert 'data' in parsed
        assert 'layout' in parsed

        # Top products
        chart_json = get_top_products_chart()
        parsed = json.loads(chart_json)
        assert 'data' in parsed
        assert 'layout' in parsed

        # Payment methods
        chart_json = get_payment_methods_chart()
        parsed = json.loads(chart_json)
        assert 'data' in parsed
        assert 'layout' in parsed

        # Monthly comparison
        chart_json = get_monthly_comparison_chart()
        parsed = json.loads(chart_json)
        assert 'data' in parsed
        assert 'layout' in parsed

        # Inventory distribution
        chart_json = get_inventory_distribution_chart()
        parsed = json.loads(chart_json)
        assert 'data' in parsed
        assert 'layout' in parsed

def test_dashboard_web_route(admin_client):
    # Default view
    resp = admin_client.get('/dashboard')
    assert resp.status_code == 200
    assert b"Net Sales Revenue" in resp.data
    assert b"Sales by Category" in resp.data

    # Filtered periods
    for p in ['today', '7d', '30d', 'this_month', 'all']:
        resp = admin_client.get(f'/dashboard?period={p}')
        assert resp.status_code == 200

from datetime import datetime, timedelta, date
from flask import Blueprint, render_template, request, session, redirect, url_for
from app.services.auth_service import login_required
from app.services.analytics_service import (
    get_kpis, get_revenue_trend_chart, get_category_sales_chart,
    get_top_products_chart, get_payment_methods_chart,
    get_monthly_comparison_chart, get_inventory_distribution_chart
)
from app.services.pos_service import get_sales_history
from app.services.inventory_service import get_low_stock_items, get_expiry_alerts

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    # If the user is a Cashier, redirect them directly to the POS screen unless they specifically requested dashboard
    if session.get('user_role') == 'CASHIER' and request.path == '/':
        return redirect(url_for('pos.index'))

    # Parse date filters
    period = request.args.get('period', '30d')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    today = date.today()
    if period == 'today':
        start_date = today.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif period == '7d':
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif period == '30d':
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif period == 'this_month':
        start_date = today.replace(day=1).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif period == 'all':
        start_date = None
        end_date = None

    kpis = get_kpis(start_date=start_date, end_date=end_date)

    # Render Plotly charts
    chart_revenue = get_revenue_trend_chart(start_date, end_date)
    chart_category = get_category_sales_chart(start_date, end_date)
    chart_top_products = get_top_products_chart(start_date, end_date)
    chart_payment_methods = get_payment_methods_chart(start_date, end_date)
    chart_monthly = get_monthly_comparison_chart()
    chart_inventory = get_inventory_distribution_chart()

    # Recent sales & alerts for dashboard widgets
    recent_sales = get_sales_history(limit=5)
    low_stock_items = get_low_stock_items()[:5]
    expiry_alerts = get_expiry_alerts()[:5]

    return render_template(
        'dashboard/index.html',
        period=period,
        start_date=start_date,
        end_date=end_date,
        kpis=kpis,
        chart_revenue=chart_revenue,
        chart_category=chart_category,
        chart_top_products=chart_top_products,
        chart_payment_methods=chart_payment_methods,
        chart_monthly=chart_monthly,
        chart_inventory=chart_inventory,
        recent_sales=recent_sales,
        low_stock_items=low_stock_items,
        expiry_alerts=expiry_alerts
    )

import json
import sqlite3
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from app.database import get_db

COLOR_PALETTE = [
    '#D97945',  # Terracotta Primary
    '#17263C',  # Deep Navy Primary
    '#6B8E68',  # Muted Forest Sage
    '#E2A053',  # Warm Amber
    '#2B4162',  # Midnight Slate
    '#B86B77',  # Rose Ochre
    '#8DA285',  # Soft Sage
    '#4A6572',  # Slate Blue
    '#9C7C5A',  # Warm Cinnamon
    '#385A48',  # Pine Slate
    '#C46736',  # Burnt Terracotta
    '#607274'   # Deep Slate Sage
]

CHART_LAYOUT_DEFAULTS = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color='#2D3748', size=12),
    margin=dict(l=40, r=30, t=40, b=40),
    hoverlabel=dict(bgcolor='#17263C', font_size=12, font_color='#FFFFFF')
)

def get_kpis(start_date=None, end_date=None):
    """Calculate key performance indicators from SQLite."""
    db = get_db()
    cursor = db.cursor()

    query = """
        SELECT
            COUNT(*) AS total_transactions,
            COALESCE(SUM(subtotal), 0) AS total_gross_sales,
            COALESCE(SUM(final_total), 0) AS total_revenue,
            COALESCE(AVG(final_total), 0) AS average_order_value,
            COALESCE(SUM(discount_amount), 0) AS total_discounts,
            COALESCE(SUM(tax_amount), 0) AS total_tax_collected
        FROM sales
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date(created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(created_at) <= date(?)"
        params.append(end_date)

    cursor.execute(query, params)
    kpi_row = dict(cursor.fetchone() or {})

    # Product metrics (current status)
    cursor.execute("""
        SELECT
            COUNT(*) AS total_skus,
            COALESCE(SUM(quantity), 0) AS total_units_in_stock,
            COALESCE(SUM(quantity * cost_price), 0) AS total_inventory_cost_value,
            COALESCE(SUM(quantity * selling_price), 0) AS total_inventory_retail_value,
            SUM(CASE WHEN quantity <= min_stock_level THEN 1 ELSE 0 END) AS low_stock_count,
            SUM(CASE WHEN expiry_date IS NOT NULL AND date(expiry_date) <= date('now', '+30 days') THEN 1 ELSE 0 END) AS expiring_count
        FROM products
    """)
    prod_row = dict(cursor.fetchone() or {})
    kpi_row.update(prod_row)

    return kpi_row

def get_revenue_trend_chart(start_date=None, end_date=None):
    """Plotly daily & monthly revenue trend line/area chart."""
    db = get_db()
    query = """
        SELECT date(created_at) AS sale_date,
               COUNT(id) AS transaction_count,
               SUM(final_total) AS revenue
        FROM sales
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date(created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(created_at) <= date(?)"
        params.append(end_date)
    query += " GROUP BY date(created_at) ORDER BY date(created_at) ASC"

    df = pd.read_sql_query(query, db, params=params)

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No sales data recorded for the selected period",
                           showarrow=False, font=dict(size=14, color="#64748B"))
        fig.update_layout(**CHART_LAYOUT_DEFAULTS)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['sale_date'],
        y=df['revenue'],
        mode='lines+markers',
        name='Daily Revenue ($)',
        line=dict(color='#D97945', width=3, shape='spline'),
        marker=dict(size=6, color='#17263C', line=dict(color='#FFFFFF', width=1.5)),
        fill='tozeroy',
        fillcolor='rgba(217, 121, 69, 0.12)',
        hovertemplate='<b>Date:</b> %{x}<br><b>Revenue:</b> $%{y:,.2f}<extra></extra>'
    ))

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        xaxis=dict(showgrid=True, gridcolor='#E8E2D8', title='Date', tickangle=-30),
        yaxis=dict(showgrid=True, gridcolor='#E8E2D8', title='Revenue ($)', tickprefix='$')
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def get_category_sales_chart(start_date=None, end_date=None):
    """Plotly Donut chart for sales distribution by category."""
    db = get_db()
    query = """
        SELECT p.category,
               SUM(si.line_total) AS total_revenue,
               SUM(si.quantity) AS total_units_sold
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        JOIN products p ON si.product_id = p.id
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date(s.created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(s.created_at) <= date(?)"
        params.append(end_date)
    query += " GROUP BY p.category ORDER BY total_revenue DESC"

    df = pd.read_sql_query(query, db, params=params)

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No sales recorded by category", showarrow=False,
                           font=dict(size=14, color="#64748B", family='Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'))
        fig.update_layout(**CHART_LAYOUT_DEFAULTS)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    colors = [COLOR_PALETTE[i % len(COLOR_PALETTE)] for i in range(len(df))]

    fig = go.Figure(data=[go.Pie(
        labels=df['category'],
        values=df['total_revenue'],
        hole=0.52,
        domain=dict(x=[0, 1], y=[0.24, 1.0]),
        marker=dict(
            colors=colors,
            line=dict(color='#FFFFFF', width=2.5)
        ),
        textinfo='percent',
        textposition='inside',
        insidetextorientation='horizontal',
        insidetextfont=dict(family='Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', size=11, color='#FFFFFF'),
        hovertemplate='<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Share: <b>%{percent}</b><extra></extra>',
        sort=False
    )])

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color='#1F2937', size=11),
        margin=dict(l=10, r=10, t=10, b=10),
        hoverlabel=dict(bgcolor='#17263C', font_size=12, font_color='#FFFFFF', font_family='Inter, sans-serif'),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=0.20,
            xanchor="center",
            x=0.5,
            font=dict(size=10, family='Inter, -apple-system, sans-serif', color='#17263C')
        )
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def get_top_products_chart(start_date=None, end_date=None, limit=10):
    """Horizontal bar chart showing top 10 selling products."""
    db = get_db()
    query = """
        SELECT si.product_name,
               SUM(si.quantity) AS total_quantity,
               SUM(si.line_total) AS total_revenue
        FROM sale_items si
        JOIN sales s ON si.sale_id = s.id
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date(s.created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(s.created_at) <= date(?)"
        params.append(end_date)
    query += f" GROUP BY si.product_id ORDER BY total_revenue DESC LIMIT {limit}"

    df = pd.read_sql_query(query, db, params=params)

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No product sales recorded yet", showarrow=False, font=dict(size=14, color="#64748B"))
        fig.update_layout(**CHART_LAYOUT_DEFAULTS)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Sort ascending for horizontal bar chart display
    df = df.sort_values(by='total_revenue', ascending=True)

    fig = go.Figure(go.Bar(
        x=df['total_revenue'],
        y=df['product_name'],
        orientation='h',
        marker=dict(
            color='#17263C',
            line=dict(color='#D97945', width=1.5)
        ),
        text=[f"${val:,.2f}" for val in df['total_revenue']],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>'
    ))

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        xaxis=dict(showgrid=True, gridcolor='#E8E2D8', title='Revenue ($)', tickprefix='$'),
        yaxis=dict(title='')
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def get_payment_methods_chart(start_date=None, end_date=None):
    """Payment method breakdown chart (Cash vs Card vs UPI)."""
    db = get_db()
    query = """
        SELECT payment_method,
               COUNT(id) AS transaction_count,
               SUM(final_total) AS total_amount
        FROM sales
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date(created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(created_at) <= date(?)"
        params.append(end_date)
    query += " GROUP BY payment_method ORDER BY total_amount DESC"

    df = pd.read_sql_query(query, db, params=params)

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No payment records found", showarrow=False, font=dict(size=14, color="#64748B"))
        fig.update_layout(**CHART_LAYOUT_DEFAULTS)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    method_colors = {'CASH': '#7F9A7D', 'CARD': '#17263C', 'UPI': '#D97945'}
    colors = [method_colors.get(m, '#937D64') for m in df['payment_method']]

    fig = go.Figure(data=[go.Bar(
        x=df['payment_method'],
        y=df['total_amount'],
        marker=dict(color=colors),
        text=[f"${val:,.2f}<br>({cnt} txns)" for val, cnt in zip(df['total_amount'], df['transaction_count'])],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Total: $%{y:,.2f}<extra></extra>'
    )])

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        xaxis=dict(title='Payment Method'),
        yaxis=dict(showgrid=True, gridcolor='#E8E2D8', title='Total Processed ($)', tickprefix='$')
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def get_monthly_comparison_chart():
    """Bar chart comparing monthly sales over recent months."""
    db = get_db()
    query = """
        SELECT strftime('%Y-%m', created_at) AS month_year,
               COUNT(id) AS transactions,
               SUM(final_total) AS revenue
        FROM sales
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY month_year ASC
        LIMIT 12
    """
    df = pd.read_sql_query(query, db)

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No historical monthly data", showarrow=False, font=dict(size=14, color="#64748B"))
        fig.update_layout(**CHART_LAYOUT_DEFAULTS)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    fig = go.Figure(data=[go.Bar(
        x=df['month_year'],
        y=df['revenue'],
        marker=dict(color='#D97945'),
        text=[f"${v:,.2f}" for v in df['revenue']],
        textposition='outside',
        hovertemplate='<b>Month:</b> %{x}<br><b>Revenue:</b> $%{y:,.2f}<extra></extra>'
    )])

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        xaxis=dict(title='Month (YYYY-MM)'),
        yaxis=dict(showgrid=True, gridcolor='#E8E2D8', title='Monthly Revenue ($)', tickprefix='$')
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def get_inventory_distribution_chart():
    """Bar chart showing inventory stock valuation by product category."""
    db = get_db()
    query = """
        SELECT category,
               COUNT(id) AS sku_count,
               SUM(quantity) AS total_units,
               SUM(quantity * selling_price) AS retail_valuation,
               SUM(quantity * cost_price) AS cost_valuation
        FROM products
        GROUP BY category
        ORDER BY retail_valuation DESC
    """
    df = pd.read_sql_query(query, db)

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No inventory data found", showarrow=False, font=dict(size=14, color="#64748B"))
        fig.update_layout(**CHART_LAYOUT_DEFAULTS)
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['category'],
        y=df['cost_valuation'],
        name='Cost Valuation',
        marker=dict(color='#7F9A7D')
    ))
    fig.add_trace(go.Bar(
        x=df['category'],
        y=df['retail_valuation'],
        name='Retail Valuation',
        marker=dict(color='#17263C')
    ))

    fig.update_layout(
        **CHART_LAYOUT_DEFAULTS,
        barmode='group',
        xaxis=dict(title='Category', tickangle=-25),
        yaxis=dict(showgrid=True, gridcolor='#E8E2D8', title='Valuation ($)', tickprefix='$'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

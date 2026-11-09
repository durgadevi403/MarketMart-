from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import login_required, role_required
from app.services.inventory_service import (
    adjust_stock, get_stock_movements, get_low_stock_items,
    get_expiry_alerts, get_inventory_summary
)
from app.services.product_service import get_all_products, get_categories

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
@login_required
@role_required(['ADMIN'])
def index():
    category = request.args.get('category', 'All')
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()

    products = get_all_products(
        search=search if search else None,
        category=category,
        stock_status=status if status else None,
        sort_by='quantity',
        order='asc'
    )
    summary = get_inventory_summary()
    categories = get_categories()

    return render_template(
        'inventory/stock_levels.html',
        products=products,
        summary=summary,
        categories=categories,
        selected_category=category,
        selected_status=status,
        search=search
    )

@inventory_bp.route('/adjust', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def adjust():
    product_id = request.form.get('product_id')
    movement_type = request.form.get('movement_type')
    quantity_change = request.form.get('quantity_change')
    reason = request.form.get('reason')

    try:
        adjust_stock(
            product_id=int(product_id),
            quantity_change=int(quantity_change),
            movement_type=movement_type,
            reason=reason,
            user_id=session.get('user_id')
        )
        flash("Stock adjustment logged and updated successfully.", "success")
    except Exception as e:
        flash(str(e), "danger")

    return redirect(request.referrer or url_for('inventory.index'))

@inventory_bp.route('/movements')
@login_required
@role_required(['ADMIN'])
def movements():
    movement_type = request.args.get('type', 'All')
    limit = int(request.args.get('limit', 150))
    records = get_stock_movements(movement_type=movement_type, limit=limit)
    return render_template('inventory/movements.html', movements=records, selected_type=movement_type)

@inventory_bp.route('/reorder')
@login_required
@role_required(['ADMIN'])
def reorder():
    items = get_low_stock_items()
    return render_template('inventory/reorder.html', items=items)

@inventory_bp.route('/expiries')
@login_required
@role_required(['ADMIN'])
def expiries():
    alerts = get_expiry_alerts()
    return render_template('inventory/expiries.html', alerts=alerts)

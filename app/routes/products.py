from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.services.auth_service import login_required, role_required
from app.services.product_service import (
    get_all_products, get_product_by_id, get_categories,
    create_product, update_product, delete_product
)
from app.services.supplier_service import get_all_suppliers

products_bp = Blueprint('products', __name__)

@products_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', 'All')
    supplier_id = request.args.get('supplier_id', 'All')
    stock_status = request.args.get('stock_status', '')
    sort_by = request.args.get('sort_by', 'name')
    order = request.args.get('order', 'asc')

    products = get_all_products(
        search=search if search else None,
        category=category,
        supplier_id=supplier_id,
        stock_status=stock_status if stock_status else None,
        sort_by=sort_by,
        order=order
    )
    categories = get_categories()
    suppliers = get_all_suppliers()

    return render_template(
        'products/list.html',
        products=products,
        categories=categories,
        suppliers=suppliers,
        selected_search=search,
        selected_category=category,
        selected_supplier=supplier_id,
        selected_status=stock_status,
        sort_by=sort_by,
        order=order
    )

@products_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def create():
    categories = get_categories()
    suppliers = get_all_suppliers()

    if request.method == 'POST':
        name = request.form.get('name')
        sku = request.form.get('sku')
        category = request.form.get('category')
        custom_category = request.form.get('custom_category', '').strip()
        if category == 'NEW' and custom_category:
            category = custom_category

        description = request.form.get('description')
        cost_price = request.form.get('cost_price')
        selling_price = request.form.get('selling_price')
        quantity = request.form.get('quantity', 0)
        min_stock_level = request.form.get('min_stock_level', 5)
        expiry_date = request.form.get('expiry_date')
        supplier_id = request.form.get('supplier_id')

        try:
            prod_id = create_product(
                name=name,
                sku=sku,
                category=category,
                description=description,
                cost_price=cost_price,
                selling_price=selling_price,
                quantity=quantity,
                min_stock_level=min_stock_level,
                expiry_date=expiry_date,
                supplier_id=supplier_id,
                user_id=session.get('user_id')
            )
            flash(f"Product '{name}' created successfully.", "success")
            return redirect(url_for('products.index'))
        except Exception as e:
            flash(str(e), "danger")
            return render_template(
                'products/form.html',
                action='Create',
                product=request.form,
                categories=categories,
                suppliers=suppliers
            )

    return render_template(
        'products/form.html',
        action='Create',
        product={},
        categories=categories,
        suppliers=suppliers
    )

@products_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def edit(product_id):
    product = get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "warning")
        return redirect(url_for('products.index'))

    categories = get_categories()
    suppliers = get_all_suppliers()

    if request.method == 'POST':
        name = request.form.get('name')
        sku = request.form.get('sku')
        category = request.form.get('category')
        custom_category = request.form.get('custom_category', '').strip()
        if category == 'NEW' and custom_category:
            category = custom_category

        description = request.form.get('description')
        cost_price = request.form.get('cost_price')
        selling_price = request.form.get('selling_price')
        min_stock_level = request.form.get('min_stock_level', 5)
        expiry_date = request.form.get('expiry_date')
        supplier_id = request.form.get('supplier_id')

        try:
            update_product(
                product_id=product_id,
                name=name,
                sku=sku,
                category=category,
                description=description,
                cost_price=cost_price,
                selling_price=selling_price,
                min_stock_level=min_stock_level,
                expiry_date=expiry_date,
                supplier_id=supplier_id
            )
            flash(f"Product '{name}' updated successfully.", "success")
            return redirect(url_for('products.index'))
        except Exception as e:
            flash(str(e), "danger")
            return render_template(
                'products/form.html',
                action='Edit',
                product={**product, **dict(request.form)},
                categories=categories,
                suppliers=suppliers
            )

    return render_template(
        'products/form.html',
        action='Edit',
        product=product,
        categories=categories,
        suppliers=suppliers
    )

@products_bp.route('/<int:product_id>/delete', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def delete(product_id):
    try:
        delete_product(product_id)
        flash("Product successfully removed.", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for('products.index'))

@products_bp.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', 'All')
    products = get_all_products(search=q if q else None, category=category)
    return jsonify([
        {
            'id': p['id'],
            'name': p['name'],
            'sku': p['sku'],
            'category': p['category'],
            'selling_price': p['selling_price'],
            'quantity': p['quantity'],
            'min_stock_level': p['min_stock_level'],
            'expiry_date': p['expiry_date'],
            'status': p['status'],
            'badge_class': p['badge_class'],
            'label': p['label']
        }
        for p in products
    ])

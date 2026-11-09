from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from app.services.auth_service import login_required
from app.services.product_service import get_all_products, get_categories
from app.services.pos_service import process_sale, get_sale_by_invoice, get_sales_history

pos_bp = Blueprint('pos', __name__)

@pos_bp.route('/')
@login_required
def index():
    categories = get_categories()
    products = get_all_products()
    default_tax_rate = current_app.config.get('DEFAULT_TAX_RATE', 5.0)
    return render_template(
        'pos/index.html',
        categories=categories,
        products=products,
        default_tax_rate=default_tax_rate
    )

@pos_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    # Expecting JSON or Form Data
    if request.is_json:
        data = request.get_json() or {}
        items = data.get('items', [])
        customer_name = data.get('customer_name')
        customer_phone = data.get('customer_phone')
        discount_type = data.get('discount_type', 'NONE')
        discount_value = data.get('discount_value', 0.0)
        payment_method = data.get('payment_method', 'CASH')
        amount_tendered = data.get('amount_tendered', 0.0)
        notes = data.get('notes')
    else:
        # Fallback to form submission
        data = request.form
        customer_name = data.get('customer_name')
        customer_phone = data.get('customer_phone')
        discount_type = data.get('discount_type', 'NONE')
        discount_value = data.get('discount_value', 0.0)
        payment_method = data.get('payment_method', 'CASH')
        amount_tendered = data.get('amount_tendered', 0.0)
        notes = data.get('notes')
        # Form-based item parsing
        import json
        try:
            items = json.loads(data.get('items_json', '[]'))
        except Exception:
            items = []

    cashier_id = session.get('user_id')

    try:
        sale_result = process_sale(
            cart_items=items,
            cashier_id=cashier_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            discount_type=discount_type,
            discount_value=discount_value,
            payment_method=payment_method,
            amount_tendered=amount_tendered,
            notes=notes
        )

        invoice_url = url_for('pos.view_invoice', invoice_no=sale_result['invoice_no'])
        if request.is_json:
            return jsonify({
                'success': True,
                'invoice_no': sale_result['invoice_no'],
                'sale': sale_result,
                'invoice_url': invoice_url
            })
        else:
            flash(f"Sale processed! Invoice #{sale_result['invoice_no']} generated.", "success")
            return redirect(invoice_url)

    except ValueError as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        else:
            flash(str(e), "danger")
            return redirect(url_for('pos.index'))
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': f"Transaction failed: {str(e)}"}), 500
        else:
            flash(f"Transaction failed: {str(e)}", "danger")
            return redirect(url_for('pos.index'))

@pos_bp.route('/invoice/<invoice_no>')
@login_required
def view_invoice(invoice_no):
    sale = get_sale_by_invoice(invoice_no)
    if not sale:
        flash(f"Invoice '{invoice_no}' was not found.", "warning")
        return redirect(url_for('pos.index'))
    return render_template('pos/invoice.html', sale=sale)

@pos_bp.route('/history')
@login_required
def history():
    user_role = session.get('user_role')
    user_id = session.get('user_id')

    search = request.args.get('search', '').strip()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Cashiers can view transactions; Admins can see all
    cashier_filter = None if user_role == 'ADMIN' else user_id

    sales = get_sales_history(
        search=search if search else None,
        start_date=start_date,
        end_date=end_date,
        cashier_id=cashier_filter,
        limit=100
    )

    return render_template(
        'pos/history.html',
        sales=sales,
        search=search,
        start_date=start_date,
        end_date=end_date
    )

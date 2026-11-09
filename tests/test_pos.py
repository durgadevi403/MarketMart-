import pytest
from app.services.pos_service import (
    process_sale, calculate_totals, get_sale_by_invoice, get_sales_history
)
from app.services.product_service import get_product_by_id

def test_pure_calculation_helper():
    # 2 items at $10.00 each -> subtotal = $20.00
    mock_items = [{'unit_price': 10.0, 'quantity': 2}]

    # No discount, 5% tax
    res = calculate_totals(mock_items, discount_type='NONE', discount_value=0.0, tax_rate=5.0)
    assert res['subtotal'] == 20.00
    assert res['discount_amount'] == 0.0
    assert res['tax_amount'] == 1.00 # 5% of 20
    assert res['final_total'] == 21.00

    # 10% percentage discount
    res = calculate_totals(mock_items, discount_type='PERCENTAGE', discount_value=10.0, tax_rate=5.0)
    assert res['subtotal'] == 20.00
    assert res['discount_amount'] == 2.00
    # Taxable = 18.00, 5% of 18 = 0.90
    assert res['tax_amount'] == 0.90
    assert res['final_total'] == 18.90

    # Fixed discount $5.00
    res = calculate_totals(mock_items, discount_type='FIXED', discount_value=5.0, tax_rate=5.0)
    assert res['discount_amount'] == 5.00
    # Taxable = 15.00, 5% of 15 = 0.75
    assert res['tax_amount'] == 0.75
    assert res['final_total'] == 15.75

def test_discount_boundary_validations():
    mock_items = [{'unit_price': 10.0, 'quantity': 2}]

    # Negative discount
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_totals(mock_items, discount_type='PERCENTAGE', discount_value=-5.0)

    # Percentage > 100%
    with pytest.raises(ValueError, match="cannot exceed 100%"):
        calculate_totals(mock_items, discount_type='PERCENTAGE', discount_value=120.0)

    # Fixed discount > subtotal
    with pytest.raises(ValueError, match="cannot exceed subtotal"):
        calculate_totals(mock_items, discount_type='FIXED', discount_value=50.0)

def test_process_sale_and_inventory_deduction(app):
    with app.app_context():
        # Choose product 1
        prod_before = get_product_by_id(1)
        start_qty = prod_before['quantity']
        assert start_qty >= 2

        cart = [{'product_id': 1, 'quantity': 2}]
        sale = process_sale(
            cart_items=cart,
            cashier_id=2,
            customer_name="Alice Smith",
            customer_phone="+15551234567",
            discount_type='PERCENTAGE',
            discount_value=10.0,
            payment_method='CASH',
            amount_tendered=100.0,
            notes='Test POS Sale'
        )

        assert sale is not None
        assert 'invoice_no' in sale
        assert sale['invoice_no'].startswith('INV-')
        assert sale['payment_method'] == 'CASH'
        assert sale['amount_tendered'] == 100.0
        assert sale['change_returned'] == round(100.0 - sale['final_total'], 2)

        # Verify stock was deducted in database
        prod_after = get_product_by_id(1)
        assert prod_after['quantity'] == start_qty - 2

        # Verify invoice lookup
        inv_data = get_sale_by_invoice(sale['invoice_no'])
        assert inv_data is not None
        assert inv_data['customer_name'] == "Alice Smith"
        assert len(inv_data['items']) == 1
        assert inv_data['items'][0]['quantity'] == 2

def test_insufficient_stock_rejection(app):
    with app.app_context():
        prod = get_product_by_id(1)
        current_stock = prod['quantity']

        # Request more stock than available
        cart = [{'product_id': 1, 'quantity': current_stock + 50}]
        with pytest.raises(ValueError, match="Insufficient stock"):
            process_sale(
                cart_items=cart,
                cashier_id=2,
                payment_method='CARD'
            )

        # Ensure stock remained unchanged
        prod_after = get_product_by_id(1)
        assert prod_after['quantity'] == current_stock

def test_cash_tendered_too_low(app):
    with app.app_context():
        cart = [{'product_id': 1, 'quantity': 1}]
        with pytest.raises(ValueError, match="Cash tendered .* is less than total payable"):
            process_sale(
                cart_items=cart,
                cashier_id=2,
                payment_method='CASH',
                amount_tendered=0.50 # Tiny amount
            )

def test_pos_web_checkout_and_invoice_view(cashier_client):
    # Cashier processes checkout via JSON API
    payload = {
        'items': [{'product_id': 1, 'quantity': 1}],
        'customer_name': 'Walk-in Bob',
        'discount_type': 'NONE',
        'discount_value': 0,
        'payment_method': 'CARD',
        'amount_tendered': 0
    }

    resp = cashier_client.post('/pos/checkout', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert 'invoice_no' in data
    invoice_no = data['invoice_no']

    # View invoice receipt page
    view_resp = cashier_client.get(f'/pos/invoice/{invoice_no}')
    assert view_resp.status_code == 200
    assert invoice_no.encode() in view_resp.data
    assert b"Walk-in Bob" in view_resp.data

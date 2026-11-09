import json
import pytest
from app.services.product_service import get_product_by_id
from app.services.pos_service import process_sale

def test_price_manipulation_prevention(app):
    """
    CRITICAL SECURITY TEST:
    Verify that if the client sends a bogus/manipulated unit_price in the cart items,
    the backend strictly pulls the authoritative selling_price from the database
    and charges the correct full price.
    """
    with app.app_context():
        prod = get_product_by_id(1)
        actual_price = prod['selling_price']
        assert actual_price > 1.0 # e.g. $2.49

        # Malicious client sends $0.01 price
        manipulated_cart = [
            {'product_id': 1, 'quantity': 1, 'unit_price': 0.01, 'selling_price': 0.01, 'line_total': 0.01}
        ]

        sale = process_sale(
            cart_items=manipulated_cart,
            cashier_id=2,
            payment_method='CARD'
        )

        # Verified sale subtotal MUST equal actual database price, NOT $0.01!
        assert sale['subtotal'] == round(actual_price, 2)
        assert sale['final_total'] > 1.0

def test_zero_and_negative_quantity_rejection(app):
    """Ensure negative or zero quantities are rejected."""
    with app.app_context():
        with pytest.raises(ValueError, match="must be greater than zero"):
            process_sale(
                cart_items=[{'product_id': 1, 'quantity': 0}],
                cashier_id=2,
                payment_method='CARD'
            )

        with pytest.raises(ValueError, match="must be greater than zero"):
            process_sale(
                cart_items=[{'product_id': 1, 'quantity': -3}],
                cashier_id=2,
                payment_method='CARD'
            )

def test_sql_injection_defense(client, admin_client):
    """Ensure search queries with injection patterns are parameterized and safe."""
    sql_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE products; --",
        "1' UNION SELECT username, password_hash FROM users --"
    ]

    for payload in sql_payloads:
        # Search products
        resp = admin_client.get(f'/products/?search={payload}')
        assert resp.status_code == 200

        # Search suppliers
        resp = admin_client.get(f'/suppliers/?search={payload}')
        assert resp.status_code == 200

        # Date range in reports
        resp = admin_client.get(f'/reports/daily-sales?start_date={payload}')
        assert resp.status_code == 200

def test_unauthorized_admin_mutation_by_cashier(cashier_client):
    """Ensure cashier cannot create products, delete products, or delete users."""
    # Cannot create product
    resp = cashier_client.post('/products/new', data={'name': 'Hacked Prod'})
    assert resp.status_code == 403

    # Cannot delete product
    resp = cashier_client.post('/products/1/delete')
    assert resp.status_code == 403

    # Cannot delete user
    resp = cashier_client.post('/users/1/delete')
    assert resp.status_code == 403

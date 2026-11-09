import pytest
from app.services.product_service import (
    create_product, update_product, delete_product,
    get_all_products, get_product_by_id, get_product_by_sku,
    compute_stock_status
)

def test_product_crud_lifecycle(app):
    with app.app_context():
        # Create product
        prod_id = create_product(
            name="Organic Avocados Test",
            sku="TEST-AVO-999",
            category="Fresh Produce",
            description="Creamy ripe avocados test",
            cost_price=1.50,
            selling_price=3.00,
            quantity=25,
            min_stock_level=10,
            expiry_date="2026-12-31",
            supplier_id=1,
            user_id=1
        )
        assert prod_id > 0

        # Read product
        prod = get_product_by_id(prod_id)
        assert prod is not None
        assert prod['name'] == "Organic Avocados Test"
        assert prod['sku'] == "TEST-AVO-999"
        assert prod['quantity'] == 25
        assert prod['status'] == 'in_stock'

        # Read by SKU
        by_sku = get_product_by_sku("TEST-AVO-999")
        assert by_sku['id'] == prod_id

        # Update product
        updated = update_product(
            product_id=prod_id,
            name="Organic Hass Avocados Premium",
            sku="TEST-AVO-999",
            category="Fresh Produce",
            description="Updated description",
            cost_price=1.60,
            selling_price=3.25,
            min_stock_level=12,
            expiry_date="2026-12-31",
            supplier_id=1
        )
        assert updated is True
        prod = get_product_by_id(prod_id)
        assert prod['name'] == "Organic Hass Avocados Premium"
        assert prod['selling_price'] == 3.25

        # Delete product
        deleted = delete_product(prod_id)
        assert deleted is True
        assert get_product_by_id(prod_id) is None

def test_product_validation_rules(app):
    with app.app_context():
        # Duplicate SKU test
        create_product("Product A", "SKU-DUP-1", "Produce", "", 1.0, 2.0, 10, 5)
        with pytest.raises(ValueError, match="already exists"):
            create_product("Product B", "SKU-DUP-1", "Produce", "", 1.0, 2.0, 10, 5)

        # Negative cost price
        with pytest.raises(ValueError, match="Cost price cannot be negative"):
            create_product("Bad Cost", "SKU-NEG-1", "Produce", "", -1.5, 2.0, 10, 5)

        # Negative selling price
        with pytest.raises(ValueError, match="Selling price cannot be negative"):
            create_product("Bad Price", "SKU-NEG-2", "Produce", "", 1.0, -2.0, 10, 5)

        # Negative quantity
        with pytest.raises(ValueError, match="Quantity cannot be negative"):
            create_product("Bad Qty", "SKU-NEG-3", "Produce", "", 1.0, 2.0, -5, 5)

def test_compute_stock_status_logic():
    # Out of stock
    out_st = compute_stock_status(quantity=0, min_stock=10)
    assert out_st['status'] == 'out_of_stock'

    # Low stock
    low_st = compute_stock_status(quantity=5, min_stock=10)
    assert low_st['status'] == 'low_stock'

    # Adequate stock
    in_st = compute_stock_status(quantity=20, min_stock=10)
    assert in_st['status'] == 'in_stock'

def test_products_web_routes(admin_client, cashier_client):
    # Both can view product catalog
    resp_admin = admin_client.get('/products/')
    assert resp_admin.status_code == 200

    resp_cashier = cashier_client.get('/products/')
    assert resp_cashier.status_code == 200

    # API search
    api_resp = cashier_client.get('/products/api/search?q=milk')
    assert api_resp.status_code == 200
    assert api_resp.is_json
    data = api_resp.get_json()
    assert isinstance(data, list)

    # Cashier cannot POST new product (Admin only)
    resp_create = cashier_client.post('/products/new', data={
        'name': 'Unauthorized Product',
        'sku': 'NO-AUTH-1',
        'category': 'Produce',
        'cost_price': '1.0',
        'selling_price': '2.0',
        'quantity': '10',
        'min_stock_level': '5'
    })
    assert resp_create.status_code == 403

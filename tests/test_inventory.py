import pytest
from app.services.inventory_service import (
    adjust_stock, get_stock_movements, get_low_stock_items,
    get_expiry_alerts, get_inventory_summary
)
from app.services.product_service import get_product_by_id

def test_stock_adjustment_increase_and_audit(app):
    with app.app_context():
        # Pick product 1
        prod = get_product_by_id(1)
        initial_qty = prod['quantity']

        # Restock 15 units
        res = adjust_stock(
            product_id=1,
            quantity_change=15,
            movement_type='PURCHASE_RECEIPT',
            reason='Weekly restock delivery',
            user_id=1
        )
        assert res['new_quantity'] == initial_qty + 15
        assert res['previous_quantity'] == initial_qty

        # Verify product quantity updated in DB
        updated_prod = get_product_by_id(1)
        assert updated_prod['quantity'] == initial_qty + 15

        # Verify audit trail
        movements = get_stock_movements(product_id=1, limit=5)
        latest = movements[0]
        assert latest['movement_type'] == 'PURCHASE_RECEIPT'
        assert latest['quantity_change'] == 15
        assert latest['new_quantity'] == initial_qty + 15

def test_stock_adjustment_negative_inventory_rejection(app):
    with app.app_context():
        prod = get_product_by_id(1)
        current_qty = prod['quantity']

        # Attempting to deduct more than available must raise ValueError
        with pytest.raises(ValueError, match="Insufficient stock"):
            adjust_stock(
                product_id=1,
                quantity_change=-(current_qty + 10),
                movement_type='DAMAGE',
                reason='Attempted excess reduction',
                user_id=1
            )

        # Quantity must remain intact after rollback
        prod_after = get_product_by_id(1)
        assert prod_after['quantity'] == current_qty

def test_low_stock_and_reorder_recommendations(app):
    with app.app_context():
        low_items = get_low_stock_items()
        assert isinstance(low_items, list)
        for item in low_items:
            assert item['quantity'] <= item['min_stock_level']
            assert 'recommended_reorder' in item
            assert item['recommended_reorder'] > 0
            assert 'estimated_reorder_cost' in item

def test_expiry_alerts(app):
    with app.app_context():
        alerts = get_expiry_alerts()
        assert isinstance(alerts, list)
        for a in alerts:
            assert 'expiry_status' in a
            assert a['expiry_status'] in ('EXPIRED', 'EXPIRES_TODAY', 'EXPIRING_SOON')

def test_inventory_summary_metrics(app):
    with app.app_context():
        summary = get_inventory_summary()
        assert summary['total_skus'] > 0
        assert summary['total_units'] > 0
        assert summary['total_cost_valuation'] > 0
        assert summary['total_retail_valuation'] > 0
        assert summary['total_retail_valuation'] >= summary['total_cost_valuation']

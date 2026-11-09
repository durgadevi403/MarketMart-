import pytest
from app.services.supplier_service import (
    create_supplier, update_supplier, delete_supplier,
    get_all_suppliers, get_supplier_by_id
)

def test_supplier_crud_lifecycle(app):
    with app.app_context():
        # Create
        sup_id = create_supplier(
            name="Cascade Mountain Honey Co.",
            contact_person="Hannah Abbott",
            phone="+1 (555) 777-8899",
            email="hannah@cascademountain.com",
            address="10 Honey Lane, Bend, OR",
            notes="Bi-weekly deliveries of raw clover honey"
        )
        assert sup_id > 0

        # Read
        sup = get_supplier_by_id(sup_id)
        assert sup is not None
        assert sup['name'] == "Cascade Mountain Honey Co."
        assert sup['contact_person'] == "Hannah Abbott"

        # Update
        updated = update_supplier(
            supplier_id=sup_id,
            name="Cascade Mountain Honey & Bee Co.",
            contact_person="Hannah Abbott-Smith",
            phone="+1 (555) 777-8899",
            email="hannah.smith@cascademountain.com",
            address="12 Honey Lane, Bend, OR",
            notes="Updated terms"
        )
        assert updated is True
        sup = get_supplier_by_id(sup_id)
        assert sup['name'] == "Cascade Mountain Honey & Bee Co."

        # Delete
        deleted = delete_supplier(sup_id)
        assert deleted is True
        assert get_supplier_by_id(sup_id) is None

def test_suppliers_web_routes(admin_client, cashier_client):
    # Admin can access list and create
    resp = admin_client.get('/suppliers/')
    assert resp.status_code == 200

    resp = admin_client.get('/suppliers/1')
    assert resp.status_code == 200

    # Cashier is blocked
    resp_cashier = cashier_client.get('/suppliers/')
    assert resp_cashier.status_code == 403

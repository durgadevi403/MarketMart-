import pytest
from app.services.auth_service import hash_password, verify_password, authenticate, create_user, delete_user

def test_password_hashing():
    raw = "SecureP@ss2026"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_authenticate_success(app):
    with app.app_context():
        user = authenticate("admin", "Admin@123")
        assert user is not None
        assert user['username'] == 'admin'
        assert user['role'] == 'ADMIN'

        cashier = authenticate("cashier", "Cashier@123")
        assert cashier is not None
        assert cashier['role'] == 'CASHIER'

def test_authenticate_failure(app):
    with app.app_context():
        assert authenticate("admin", "WrongPass") is None
        assert authenticate("non_existent_user", "AnyPass") is None

def test_login_flow(client):
    # GET login page
    resp = client.get('/auth/login')
    assert resp.status_code == 200
    assert b"Sign In to MarketMate" in resp.data

    # POST login success
    resp = client.post('/auth/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Signed in as ADMIN" in resp.data

    # Logout
    resp = client.get('/auth/logout', follow_redirects=True)
    assert resp.status_code == 200
    assert b"signed out successfully" in resp.data

def test_role_based_access_control(client, admin_client, cashier_client):
    # Unauthenticated user visiting admin page redirects to login
    resp = client.get('/users/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/auth/login' in resp.headers['Location']

    # Cashier attempting to access Admin-only Users list should get 403 Forbidden!
    resp = cashier_client.get('/users/')
    assert resp.status_code == 403

    # Cashier attempting to access Admin-only Suppliers list should get 403!
    resp = cashier_client.get('/suppliers/')
    assert resp.status_code == 403

    # Cashier attempting to access Admin-only Inventory management should get 403!
    resp = cashier_client.get('/inventory/')
    assert resp.status_code == 403

    # Admin accessing users and suppliers succeeds (200)
    resp = admin_client.get('/users/')
    assert resp.status_code == 200

    resp = admin_client.get('/suppliers/')
    assert resp.status_code == 200

def test_user_creation_and_validation(app):
    with app.app_context():
        # Valid user
        uid = create_user("testclerk", "Clerk@123", "Test Clerk", "clerk@test.com", "CASHIER")
        assert uid > 0

        # Duplicate username should raise ValueError
        with pytest.raises(ValueError, match="already taken"):
            create_user("testclerk", "Clerk@123", "Another Clerk", "clerk2@test.com", "CASHIER")

        # Duplicate email should raise ValueError
        with pytest.raises(ValueError, match="already registered"):
            create_user("newuser", "Clerk@123", "Duplicate Email", "clerk@test.com", "CASHIER")

        # Invalid short password
        with pytest.raises(ValueError, match="at least 6 characters"):
            create_user("shortpass", "123", "Short Pass", "short@test.com", "CASHIER")

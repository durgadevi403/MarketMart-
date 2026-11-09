import os
import pytest
from app import create_app
from app.database import init_db, connect_db
from seed_data import seed_database

@pytest.fixture(scope='session')
def app():
    os.environ['FLASK_ENV'] = 'testing'
    app = create_app('testing')
    
    # Initialize and seed test database
    db_path = app.config['DATABASE_PATH']
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
            
    init_db(db_path)
    seed_database(db_path)

    yield app

    # Cleanup after test session
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

@pytest.fixture
def client(app):
    """Clean, unauthenticated test client."""
    return app.test_client()

@pytest.fixture
def db_conn(app):
    conn = connect_db(app.config['DATABASE_PATH'])
    yield conn
    conn.close()

@pytest.fixture
def admin_client(app):
    """Isolated client authenticated as Admin (Victoria Sterling)."""
    c = app.test_client()
    c.post('/auth/login', data={'username': 'admin', 'password': 'Admin@123'}, follow_redirects=True)
    return c

@pytest.fixture
def cashier_client(app):
    """Isolated client authenticated as Cashier (Liam Vance)."""
    c = app.test_client()
    c.post('/auth/login', data={'username': 'cashier', 'password': 'Cashier@123'}, follow_redirects=True)
    return c

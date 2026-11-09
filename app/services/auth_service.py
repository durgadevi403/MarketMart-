import functools
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, redirect, url_for, flash, abort, g
from app.database import get_db

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)

def authenticate(username: str, password: str):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, password_hash, full_name, email, role, is_active FROM users WHERE username = ?",
        (username.strip(),)
    )
    user = cursor.fetchone()
    if user and user['is_active'] and verify_password(password, user['password_hash']):
        return dict(user)
    return None

def get_user_by_id(user_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, full_name, email, role, is_active, created_at FROM users WHERE id = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    return dict(user) if user else None

def get_user_by_username(username: str):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, full_name, email, role, is_active, created_at FROM users WHERE username = ?",
        (username.strip(),)
    )
    user = cursor.fetchone()
    return dict(user) if user else None

def get_all_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, full_name, email, role, is_active, created_at FROM users ORDER BY id ASC"
    )
    return [dict(row) for row in cursor.fetchall()]

def create_user(username: str, password: str, full_name: str, email: str, role: str, is_active: int = 1):
    username = username.strip()
    email = email.strip().lower()
    full_name = full_name.strip()
    role = role.strip().upper()

    if not username or len(username) < 3:
        raise ValueError("Username must be at least 3 characters long.")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    if not full_name:
        raise ValueError("Full name is required.")
    if not email or '@' not in email:
        raise ValueError("A valid email address is required.")
    if role not in ('ADMIN', 'CASHIER'):
        raise ValueError("Role must be either ADMIN or CASHIER.")

    db = get_db()
    cursor = db.cursor()
    hashed = hash_password(password)
    try:
        cursor.execute(
            """INSERT INTO users (username, password_hash, full_name, email, role, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username, hashed, full_name, email, role, 1 if is_active else 0)
        )
        db.commit()
        return cursor.lastrowid
    except Exception as e:
        db.rollback()
        if 'UNIQUE constraint failed: users.username' in str(e):
            raise ValueError(f"Username '{username}' is already taken.")
        if 'UNIQUE constraint failed: users.email' in str(e):
            raise ValueError(f"Email '{email}' is already registered.")
        raise

def update_user(user_id: int, full_name: str, email: str, role: str, is_active: int = 1, new_password: str = None):
    full_name = full_name.strip()
    email = email.strip().lower()
    role = role.strip().upper()

    if not full_name:
        raise ValueError("Full name is required.")
    if not email or '@' not in email:
        raise ValueError("A valid email address is required.")
    if role not in ('ADMIN', 'CASHIER'):
        raise ValueError("Role must be either ADMIN or CASHIER.")

    db = get_db()
    cursor = db.cursor()
    try:
        if new_password and len(new_password.strip()) > 0:
            if len(new_password.strip()) < 6:
                raise ValueError("New password must be at least 6 characters long.")
            hashed = hash_password(new_password.strip())
            cursor.execute(
                """UPDATE users
                   SET full_name = ?, email = ?, role = ?, is_active = ?, password_hash = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (full_name, email, role, 1 if is_active else 0, hashed, user_id)
            )
        else:
            cursor.execute(
                """UPDATE users
                   SET full_name = ?, email = ?, role = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (full_name, email, role, 1 if is_active else 0, user_id)
            )
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        if 'UNIQUE constraint failed: users.email' in str(e):
            raise ValueError(f"Email '{email}' is already registered to another user.")
        raise

def delete_user(user_id: int, current_user_id: int):
    if user_id == current_user_id:
        raise ValueError("You cannot delete your own active account.")
    db = get_db()
    cursor = db.cursor()
    # Check if this is the last admin
    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if target and target['role'] == 'ADMIN':
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'ADMIN' AND is_active = 1")
        admin_count = cursor.fetchone()['count']
        if admin_count <= 1:
            raise ValueError("Cannot delete the sole remaining active administrator.")
    try:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise

# Decorators for route protection
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access MarketMate.", "warning")
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

def role_required(allowed_roles):
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if 'user_id' not in session:
                flash("Please sign in to continue.", "warning")
                return redirect(url_for('auth.login'))
            user_role = session.get('user_role')
            if user_role not in allowed_roles:
                abort(403)
            return view(**kwargs)
        return wrapped_view
    return decorator

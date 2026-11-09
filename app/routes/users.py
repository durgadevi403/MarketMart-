from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import (
    login_required, role_required, get_all_users, get_user_by_id,
    create_user, update_user, delete_user
)

users_bp = Blueprint('users', __name__)

@users_bp.route('/')
@login_required
@role_required(['ADMIN'])
def index():
    users = get_all_users()
    return render_template('users/list.html', users=users)

@users_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def create():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        role = request.form.get('role', 'CASHIER')
        is_active = 1 if request.form.get('is_active') == '1' else 0

        try:
            create_user(username, password, full_name, email, role, is_active)
            flash(f"User account '{username}' created successfully.", "success")
            return redirect(url_for('users.index'))
        except Exception as e:
            flash(str(e), "danger")
            return render_template('users/form.html', action='Create', user=request.form)

    return render_template('users/form.html', action='Create', user={'is_active': 1, 'role': 'CASHIER'})

@users_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def edit(user_id):
    user = get_user_by_id(user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for('users.index'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        role = request.form.get('role', user['role'])
        is_active = 1 if request.form.get('is_active') == '1' else 0
        new_password = request.form.get('new_password')

        try:
            update_user(user_id, full_name, email, role, is_active, new_password if new_password else None)
            flash(f"User '{user['username']}' updated successfully.", "success")
            return redirect(url_for('users.index'))
        except Exception as e:
            flash(str(e), "danger")
            return render_template('users/form.html', action='Edit', user={**user, **dict(request.form)})

    return render_template('users/form.html', action='Edit', user=user)

@users_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def delete(user_id):
    try:
        delete_user(user_id, current_user_id=session.get('user_id'))
        flash("User account deleted successfully.", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for('users.index'))

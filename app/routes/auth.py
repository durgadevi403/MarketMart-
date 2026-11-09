from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from app.services.auth_service import authenticate, get_user_by_id, update_user, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('auth/login.html', username=username)

        user = authenticate(username, password)
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['user_role'] = user['role']
            flash(f"Welcome back, {user['full_name']}! Signed in as {user['role']}.", "success")

            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('dashboard.index'))
        else:
            flash("Invalid username or password. Please verify your credentials.", "danger")
            return render_template('auth/login.html', username=username)

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if new_password and new_password != confirm_password:
            flash("New password and confirmation do not match.", "danger")
            return render_template('auth/profile.html', user=user)

        try:
            update_user(
                user_id=user['id'],
                full_name=full_name,
                email=email,
                role=user['role'],
                is_active=user['is_active'],
                new_password=new_password if new_password else None
            )
            session['full_name'] = full_name
            flash("Profile updated successfully.", "success")
            return redirect(url_for('auth.profile'))
        except Exception as e:
            flash(str(e), "danger")
            return render_template('auth/profile.html', user=user)

    return render_template('auth/profile.html', user=user)

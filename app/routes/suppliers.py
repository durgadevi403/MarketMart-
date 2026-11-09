from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.auth_service import login_required, role_required
from app.services.supplier_service import (
    get_all_suppliers, get_supplier_by_id, create_supplier,
    update_supplier, delete_supplier
)

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/')
@login_required
@role_required(['ADMIN'])
def index():
    search = request.args.get('search', '').strip()
    suppliers = get_all_suppliers(search=search if search else None)
    return render_template('suppliers/list.html', suppliers=suppliers, search=search)

@suppliers_bp.route('/<int:supplier_id>')
@login_required
@role_required(['ADMIN'])
def detail(supplier_id):
    supplier = get_supplier_by_id(supplier_id)
    if not supplier:
        flash("Supplier not found.", "warning")
        return redirect(url_for('suppliers.index'))
    return render_template('suppliers/detail.html', supplier=supplier)

@suppliers_bp.route('/new', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def create():
    if request.method == 'POST':
        name = request.form.get('name')
        contact_person = request.form.get('contact_person')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        notes = request.form.get('notes')

        try:
            create_supplier(name, contact_person, phone, email, address, notes)
            flash(f"Supplier '{name}' registered successfully.", "success")
            return redirect(url_for('suppliers.index'))
        except Exception as e:
            flash(str(e), "danger")
            return render_template('suppliers/form.html', action='Create', supplier=request.form)

    return render_template('suppliers/form.html', action='Create', supplier={})

@suppliers_bp.route('/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def edit(supplier_id):
    supplier = get_supplier_by_id(supplier_id)
    if not supplier:
        flash("Supplier not found.", "warning")
        return redirect(url_for('suppliers.index'))

    if request.method == 'POST':
        name = request.form.get('name')
        contact_person = request.form.get('contact_person')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        notes = request.form.get('notes')

        try:
            update_supplier(supplier_id, name, contact_person, phone, email, address, notes)
            flash(f"Supplier '{name}' updated successfully.", "success")
            return redirect(url_for('suppliers.index'))
        except Exception as e:
            flash(str(e), "danger")
            return render_template('suppliers/form.html', action='Edit', supplier={**supplier, **dict(request.form)})

    return render_template('suppliers/form.html', action='Edit', supplier=supplier)

@suppliers_bp.route('/<int:supplier_id>/delete', methods=['POST'])
@login_required
@role_required(['ADMIN'])
def delete(supplier_id):
    try:
        delete_supplier(supplier_id)
        flash("Supplier removed successfully.", "success")
    except Exception as e:
        flash(str(e), "danger")
    return redirect(url_for('suppliers.index'))

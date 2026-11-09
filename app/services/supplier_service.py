from app.database import get_db

def get_all_suppliers(search=None):
    db = get_db()
    cursor = db.cursor()
    query = """
        SELECT s.*, COUNT(p.id) AS product_count
        FROM suppliers s
        LEFT JOIN products p ON s.id = p.supplier_id
    """
    params = []
    if search:
        search_pattern = f"%{search.strip()}%"
        query += " WHERE s.name LIKE ? OR s.contact_person LIKE ? OR s.phone LIKE ? OR s.email LIKE ?"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    query += " GROUP BY s.id ORDER BY s.name ASC"
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

def get_supplier_by_id(supplier_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
    supplier = cursor.fetchone()
    if not supplier:
        return None
    supplier_data = dict(supplier)
    # Fetch linked products
    cursor.execute(
        "SELECT id, name, sku, category, selling_price, quantity FROM products WHERE supplier_id = ? ORDER BY name ASC",
        (supplier_id,)
    )
    supplier_data['products'] = [dict(row) for row in cursor.fetchall()]
    return supplier_data

def create_supplier(name: str, contact_person: str = None, phone: str = None,
                    email: str = None, address: str = None, notes: str = None):
    name = (name or '').strip()
    if not name:
        raise ValueError("Supplier name is required.")

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO suppliers (name, contact_person, phone, email, address, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, contact_person.strip() if contact_person else None,
         phone.strip() if phone else None,
         email.strip().lower() if email else None,
         address.strip() if address else None,
         notes.strip() if notes else None)
    )
    db.commit()
    return cursor.lastrowid

def update_supplier(supplier_id: int, name: str, contact_person: str = None, phone: str = None,
                    email: str = None, address: str = None, notes: str = None):
    name = (name or '').strip()
    if not name:
        raise ValueError("Supplier name is required.")

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """UPDATE suppliers
           SET name = ?, contact_person = ?, phone = ?, email = ?, address = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (name, contact_person.strip() if contact_person else None,
         phone.strip() if phone else None,
         email.strip().lower() if email else None,
         address.strip() if address else None,
         notes.strip() if notes else None,
         supplier_id)
    )
    db.commit()
    return True

def delete_supplier(supplier_id: int):
    db = get_db()
    cursor = db.cursor()
    # Unlink products (supplier_id set to NULL due to ON DELETE SET NULL or explicitly)
    cursor.execute("UPDATE products SET supplier_id = NULL WHERE supplier_id = ?", (supplier_id,))
    cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))
    db.commit()
    return True

import os
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app.database import connect_db, init_db

def seed_database(db_path='marketmate.db'):
    conn = connect_db(db_path)
    cursor = conn.cursor()

    # Clear existing tables
    cursor.execute("PRAGMA foreign_keys = OFF;")
    tables = ['sale_items', 'sales', 'stock_movements', 'products', 'suppliers', 'users', 'settings']
    for t in tables:
        cursor.execute(f"DELETE FROM {t};")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}';")
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()

    print("Seeding Users...")
    admin_hash = generate_password_hash("Admin@123")
    cashier_hash = generate_password_hash("Cashier@123")

    users_data = [
        ("admin", admin_hash, "Victoria Sterling", "admin@marketmate.store", "ADMIN", 1),
        ("cashier", cashier_hash, "Liam Vance", "cashier@marketmate.store", "CASHIER", 1),
        ("maya_cashier", cashier_hash, "Maya Patel", "maya.patel@marketmate.store", "CASHIER", 1)
    ]
    cursor.executemany("""
        INSERT INTO users (username, password_hash, full_name, email, role, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, users_data)
    conn.commit()

    print("Seeding Suppliers...")
    suppliers_data = [
        ("FreshHarvest Orchards", "Elena Rodriguez", "+1 (555) 432-8901", "orders@freshharvest.com", "742 Orchard Way, Yakima, WA", "Specializes in farm-fresh produce, apples, and seasonal berries."),
        ("Sunrise Dairy Farms", "Marcus Thornton", "+1 (555) 231-6789", "marcus@sunrisedairy.com", "128 Pasture Lane, Tillamook, OR", "Delivers organic milk, farm cheeses, butter, and Greek yogurts."),
        ("Golden Crust Artisan Bakery", "Clara Dupont", "+1 (555) 876-5432", "clara@goldencrust.com", "45 Boulangerie Ave, Portland, OR", "Daily fresh sourdough, brioche, whole grain baguettes, and croissants."),
        ("Heritage Grain & Pantry", "Arthur Bennett", "+1 (555) 654-3210", "supply@heritagegrain.com", "90 Silo Boulevard, Omaha, NE", "Wholesale distributor of organic grains, heirloom rice, and artisan pastas."),
        ("Apex Beverage Distro", "Sophia Zhang", "+1 (555) 789-0123", "sophia@apexbev.com", "300 Commercial Pier, Seattle, WA", "Specialty coffees, sparkling waters, cold-pressed juices, and artisanal teas."),
        ("Pinnacle Meat & Deli", "David Morales", "+1 (555) 345-6789", "sales@pinnaclemeat.com", "550 Butcher Ridge Rd, Boise, ID", "Pasture-raised poultry, dry-aged beef cuts, and deli meats.")
    ]
    cursor.executemany("""
        INSERT INTO suppliers (name, contact_person, phone, email, address, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, suppliers_data)
    conn.commit()

    today = datetime.now().date()

    print("Seeding Products (36 realistic grocery items)...")
    # Categories: Produce, Dairy & Eggs, Bakery, Beverages, Snacks, Grains & Pantry, Meat & Deli, Canned & Preserved
    # Product tuple: (name, sku, category, description, cost_price, selling_price, quantity, min_stock, expiry_offset_days, supplier_id)
    raw_products = [
        # Fresh Produce (Supplier 1: FreshHarvest)
        ("Organic Gala Apples (1 lb)", "PRD-APL-001", "Fresh Produce", "Crisp, sweet, certified organic Washington Gala apples.", 1.20, 2.49, 85, 20, 21, 1),
        ("Cavendish Bananas (Bunch)", "PRD-BAN-002", "Fresh Produce", "Fresh ripe fair-trade bananas.", 0.65, 1.49, 120, 30, 8, 1),
        ("Organic Baby Spinach (16 oz)", "PRD-SPN-003", "Fresh Produce", "Triple-washed tender organic baby spinach leaves.", 1.80, 3.99, 45, 15, 6, 1),
        ("Hass Avocados (4-Pack)", "PRD-AVO-004", "Fresh Produce", "Creamy, nutrient-rich ready-to-eat Hass avocados.", 2.20, 4.49, 12, 15, 5, 1), # Low stock
        ("Heirloom Tomatoes (1 lb)", "PRD-TOM-005", "Fresh Produce", "Vibrant, sun-ripened farm heirloom tomatoes.", 1.50, 3.29, 3, 10, -2, 1), # Expired & Low Stock
        ("English Cucumbers", "PRD-CUC-006", "Fresh Produce", "Seedless crisp English greenhouse cucumbers.", 0.85, 1.99, 38, 12, 14, 1),

        # Dairy & Eggs (Supplier 2: Sunrise Dairy)
        ("Whole Grass-Fed Milk (1 Gal)", "DRY-MLK-001", "Dairy & Eggs", "Pasteurized non-homogenized whole milk.", 2.40, 4.69, 40, 15, 12, 2),
        ("Organic Free-Range Large Eggs (12ct)", "DRY-EGG-002", "Dairy & Eggs", "Grade A pasture-raised brown large eggs.", 2.10, 4.89, 55, 20, 25, 2),
        ("Aged White Cheddar Block (8 oz)", "DRY-CHD-003", "Dairy & Eggs", "Sharp 18-month aged artisan cheddar cheese.", 2.80, 5.99, 28, 10, 90, 2),
        ("Greek Whole Milk Yogurt (32 oz)", "DRY-YOG-004", "Dairy & Eggs", "Rich and creamy plain unsweetened Greek yogurt.", 2.25, 4.79, 6, 12, 4, 2), # Low stock & Expiring soon
        ("Salted European Butter (1 lb)", "DRY-BTR-005", "Dairy & Eggs", "82% butterfat cultured churned butter.", 2.60, 5.29, 50, 15, 60, 2),
        ("Almond Milk Unsweetened (64 oz)", "DRY-ALM-006", "Dairy & Eggs", "Dairy-free plant-based barista almond milk.", 1.70, 3.49, 32, 10, 45, 2),

        # Bakery (Supplier 3: Golden Crust)
        ("Rustic Sourdough Boule", "BAK-SRD-001", "Bakery & Breads", "Naturally fermented open-crumb sourdough bread.", 2.10, 4.99, 18, 10, 4, 3), # Expiring soon
        ("Artisan French Baguette", "BAK-BAG-002", "Bakery & Breads", "Traditional crispy crust French long loaf.", 1.20, 2.89, 4, 10, 2, 3), # Low stock & Expiring soon
        ("Multi-Grain Sandwich Bread", "BAK-MLT-003", "Bakery & Breads", "Honey oat multi-seed wholesome sliced loaf.", 1.75, 3.89, 30, 10, 7, 3),
        ("Butter Croissants (4-Pack)", "BAK-CRS-004", "Bakery & Breads", "Flaky, golden-layered pure butter croissants.", 2.50, 5.49, 15, 8, 3, 3),
        ("Gluten-Free Seeded Loaf", "BAK-GFB-005", "Bakery & Breads", "Nutritious flax and sunflower seed gluten-free loaf.", 3.00, 6.49, 0, 5, 10, 3), # Out of stock

        # Beverages (Supplier 5: Apex Beverage)
        ("Cold-Pressed Valencia Orange Juice (52 oz)", "BEV-ORJ-001", "Beverages", "100% pure squeezed citrus orange juice.", 2.80, 5.49, 24, 10, 18, 5),
        ("Artisan Dark Roast Coffee Beans (12 oz)", "BEV-COF-002", "Beverages", "Whole bean single-origin Ethiopian dark roast.", 6.50, 13.99, 42, 10, 180, 5),
        ("Sparkling Mineral Water (6-Pack)", "BEV-SPW-003", "Beverages", "Naturally effervescent Italian mountain water.", 3.00, 5.99, 65, 15, 365, 5),
        ("Organic Matcha Green Tea (50g)", "BEV-MAT-004", "Beverages", "Ceremonial grade pure Uji Japanese matcha.", 9.00, 18.50, 20, 8, 200, 5),
        ("Oat Milk Cold Brew Latte (12 oz)", "BEV-CLB-005", "Beverages", "Ready-to-drink nitro draft cold brew espresso.", 1.60, 3.79, 5, 12, 15, 5), # Low stock

        # Grains & Pantry (Supplier 4: Heritage Grain)
        ("Organic Jasmine Rice (5 lbs)", "GRN-RIC-001", "Grains & Pantry", "Fragrant long-grain white Jasmine rice.", 3.50, 7.99, 70, 15, 400, 4),
        ("Italian Bronze-Cut Penne (16 oz)", "GRN-PST-002", "Grains & Pantry", "Slow-dried durum wheat semolina pasta.", 1.10, 2.79, 90, 20, 500, 4),
        ("Rolled Old-Fashioned Oats (32 oz)", "GRN-OAT-003", "Grains & Pantry", "Certified gluten-free 100% whole grain oats.", 1.80, 3.99, 52, 15, 300, 4),
        ("Extra Virgin Cold-Pressed Olive Oil (750ml)", "GRN-OIL-004", "Grains & Pantry", "Estate bottled unfiltered Mediterranean olive oil.", 7.20, 14.99, 36, 10, 450, 4),
        ("Organic Quinoa Tricolor (2 lbs)", "GRN-QUI-005", "Grains & Pantry", "Pre-washed Andean red, black, and white quinoa.", 3.20, 6.89, 44, 12, 350, 4),

        # Meat & Deli (Supplier 6: Pinnacle Meat)
        ("Boneless Skinless Chicken Breasts (2 lbs)", "MEA-CHK-001", "Meat & Deli", "Antibiotic-free air-chilled chicken cutlets.", 5.50, 10.99, 22, 10, 6, 6),
        ("Grass-Fed Ground Beef 85/15 (1 lb)", "MEA-BEE-002", "Meat & Deli", "Locally sourced lean grass-fed ground beef.", 4.20, 7.99, 18, 10, 5, 6),
        ("Smoked Applewood Bacon (12 oz)", "MEA-BAC-003", "Meat & Deli", "Thick-cut naturally smoked heritage pork bacon.", 3.80, 6.99, 35, 12, 28, 6),
        ("Wild Caught Sockeye Salmon Fillet (1 lb)", "MEA-SLM-004", "Meat & Deli", "Sustainably harvested Pacific Alaskan wild salmon.", 8.50, 16.99, 2, 8, 3, 6), # Low stock & Expiring soon

        # Snacks & Confectionery (Supplier 4: Heritage Grain)
        ("Sea Salt Kettle Potato Chips (8.5 oz)", "SNK-CHP-001", "Snacks & Confectionery", "Small-batch crunchy avocado oil cooked chips.", 1.60, 3.69, 78, 20, 120, 4),
        ("Roasted Sea Salt Almonds (16 oz)", "SNK-ALM-002", "Snacks & Confectionery", "Dry-roasted California whole natural almonds.", 4.50, 8.99, 45, 15, 180, 4),
        ("70% Dark Chocolate Bar with Sea Salt", "SNK-CHO-003", "Snacks & Confectionery", "Fair-trade single-origin Dominican cacao.", 1.40, 3.29, 60, 15, 240, 4),
        ("Organic Raw Trail Mix (12 oz)", "SNK-TRL-004", "Snacks & Confectionery", "Cranberries, pumpkin seeds, cashews, and walnuts.", 3.10, 6.49, 34, 10, 150, 4),

        # Canned & Preserved Foods (Supplier 4: Heritage Grain)
        ("Organic Garbanzo Chickpeas (15 oz)", "CND-CHK-001", "Canned & Preserved", "Low-sodium non-GMO cooked chickpeas.", 0.70, 1.69, 110, 25, 600, 4),
        ("San Marzano Whole Peeled Tomatoes (28 oz)", "CND-TOM-002", "Canned & Preserved", "DOP certified sweet Italian plum tomatoes.", 1.90, 4.29, 65, 15, 720, 4)
    ]

    product_id_map = {}
    for p in raw_products:
        name, sku, category, desc, cost, sell, qty, min_stock, exp_offset, sup_id = p
        exp_date = (today + timedelta(days=exp_offset)).strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO products (name, sku, category, description, cost_price, selling_price, quantity, min_stock_level, expiry_date, supplier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, sku, category, desc, cost, sell, qty, min_stock, exp_date, sup_id))
        p_id = cursor.lastrowid
        product_id_map[sku] = {
            'id': p_id,
            'name': name,
            'sku': sku,
            'cost_price': cost,
            'selling_price': sell,
            'category': category
        }
        # Record initial stock movement
        cursor.execute("""
            INSERT INTO stock_movements (product_id, movement_type, quantity_change, previous_quantity, new_quantity, reference_id, reason, user_id, created_at)
            VALUES (?, 'INITIAL', ?, 0, ?, 'INIT-BATCH-01', 'Initial warehouse stock count', 1, datetime('now', '-35 days'))
        """, (p_id, qty + 50, qty + 50)) # Started with more stock to account for past sales!

    conn.commit()

    print("Seeding Historical Sales (55 realistic multi-item sales over past 30 days)...")
    customers = [
        ("Eleanor Vance", "+1 (555) 301-4491"),
        ("Jackson Reed", "+1 (555) 782-9912"),
        ("Sophia Lin", "+1 (555) 492-3310"),
        ("David Miller", "+1 (555) 819-4402"),
        ("Amara Okafor", "+1 (555) 671-5589"),
        ("Lucas Bennett", "+1 (555) 203-9182"),
        ("Chloe Martin", "+1 (555) 551-7733"),
        ("Walk-in Customer", None),
        ("Walk-in Customer", None),
        ("Walk-in Customer", None),
        ("Walk-in Customer", None)
    ]

    all_skus = list(product_id_map.keys())
    cashier_ids = [2, 3] # Liam Vance and Maya Patel

    # Generate 55 transactions spaced over 30 days
    random.seed(42) # Consistent realistic data
    for i in range(1, 56):
        # Determine date offset between 0 and 30 days ago
        days_ago = (55 - i) * 30 // 55
        hour = random.randint(8, 20)
        minute = random.randint(5, 55)
        second = random.randint(10, 50)
        sale_time = (datetime.now() - timedelta(days=days_ago)).replace(hour=hour, minute=minute, second=second)
        sale_time_str = sale_time.strftime('%Y-%m-%d %H:%M:%S')

        invoice_no = f"INV-{sale_time.strftime('%Y%m%d')}-{i:04d}"
        cust_name, cust_phone = random.choice(customers)
        cashier_id = random.choice(cashier_ids)

        # Pick 2 to 5 random products for this transaction
        num_items = random.randint(2, 5)
        chosen_skus = random.sample(all_skus, num_items)

        subtotal = 0.0
        line_items = []
        for sku in chosen_skus:
            prod = product_id_map[sku]
            qty = random.randint(1, 3)
            unit_price = prod['selling_price']
            cost_price = prod['cost_price']
            line_total = round(unit_price * qty, 2)
            subtotal += line_total
            line_items.append({
                'product_id': prod['id'],
                'name': prod['name'],
                'sku': prod['sku'],
                'cost_price': cost_price,
                'unit_price': unit_price,
                'quantity': qty,
                'line_total': line_total
            })

        subtotal = round(subtotal, 2)

        # Discount logic (20% of sales get a promotional discount)
        discount_type = 'NONE'
        discount_value = 0.0
        discount_amount = 0.0
        if random.random() < 0.25:
            if random.random() < 0.6:
                discount_type = 'PERCENTAGE'
                discount_value = random.choice([5.0, 10.0, 15.0])
                discount_amount = round(subtotal * (discount_value / 100.0), 2)
            else:
                discount_type = 'FIXED'
                discount_value = min(round(random.choice([2.0, 5.0, 10.0]), 2), subtotal)
                discount_amount = discount_value

        taxable = max(0.0, subtotal - discount_amount)
        tax_rate = 5.0
        tax_amount = round(taxable * (tax_rate / 100.0), 2)
        final_total = round(taxable + tax_amount, 2)

        # Payment method
        payment_method = random.choice(['CASH', 'CARD', 'CARD', 'UPI', 'UPI'])
        if payment_method == 'CASH':
            # Round up to nearest 5 or 10
            tendered = float(((int(final_total) // 5) + 1) * 5)
            if tendered < final_total:
                tendered += 5.0
            change = round(tendered - final_total, 2)
        else:
            tendered = final_total
            change = 0.0

        # Insert sale
        cursor.execute("""
            INSERT INTO sales (
                invoice_no, cashier_id, customer_name, customer_phone,
                subtotal, discount_type, discount_value, discount_amount,
                tax_rate, tax_amount, final_total, payment_method,
                amount_tendered, change_returned, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_no, cashier_id, cust_name, cust_phone,
            subtotal, discount_type, discount_value, discount_amount,
            tax_rate, tax_amount, final_total, payment_method,
            tendered, change, sale_time_str
        ))
        sale_id = cursor.lastrowid

        # Insert sale_items and stock_movements
        for it in line_items:
            cursor.execute("""
                INSERT INTO sale_items (
                    sale_id, product_id, product_name, product_sku,
                    cost_price, unit_price, quantity, line_total, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sale_id, it['product_id'], it['name'], it['sku'],
                it['cost_price'], it['unit_price'], it['quantity'], it['line_total'],
                sale_time_str
            ))

            cursor.execute("""
                INSERT INTO stock_movements (
                    product_id, movement_type, quantity_change, previous_quantity,
                    new_quantity, reference_id, reason, user_id, created_at
                ) VALUES (?, 'SALE', ?, 50, ?, ?, ?, ?, ?)
            """, (
                it['product_id'], -it['quantity'], 50 - it['quantity'],
                invoice_no, f"POS Sale {invoice_no}", cashier_id, sale_time_str
            ))

    # A few manual stock adjustments for audit trail variety
    adj_samples = [
        (product_id_map['PRD-TOM-005']['id'], 'EXPIRY', -5, 8, 3, 'ADJ-EXP-001', 'Damaged and spoiled during shelf inspection', 1, (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')),
        (product_id_map['BAK-GFB-005']['id'], 'DAMAGE', -3, 3, 0, 'ADJ-DMG-002', 'Packaging torn in transit', 1, (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')),
        (product_id_map['DRY-MLK-001']['id'], 'PURCHASE_RECEIPT', 25, 15, 40, 'PO-2026-908', 'Weekly fresh dairy restock delivery', 1, (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'))
    ]
    for adj in adj_samples:
        cursor.execute("""
            INSERT INTO stock_movements (product_id, movement_type, quantity_change, previous_quantity, new_quantity, reference_id, reason, user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, adj)

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == '__main__':
    from config import Config
    init_db(Config.DATABASE_PATH)
    seed_database(Config.DATABASE_PATH)

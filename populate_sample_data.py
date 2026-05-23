import sqlite3
import os

DB_PATH = os.path.join('database', 'heritage_tracker.db')

def insert_sample_data():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON;')
    cur = conn.cursor()
    try:
        # 1. Users — one per role (matching login page demo credentials)
        cur.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES ('admin_user', 'admin_user$admin', 'Aravind Swamy', 'admin@heritage.com', 'Admin')
        """)
        cur.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES ('inv_mgr', 'inv_mgr$inv', 'Lakshmi Devi', 'lakshmi@heritage.com', 'Inventory Manager')
        """)
        cur.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES ('qc_inspect', 'qc_inspect$qc', 'Suresh Nair', 'suresh@heritage.com', 'QC Inspector')
        """)
        cur.execute("""
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES ('fin_mgr', 'fin_mgr$fin', 'Priya Menon', 'priya@heritage.com', 'Finance Manager')
        """)
        # 2. Artisans
        cur.execute("""
            INSERT INTO artisans (first_name, last_name, phone, email, experience_years, skill_level, specialization, base_wage_rate)
            VALUES ('Ravi', 'Kumar', '555-0101', 'ravi@example.com', 12, 'Master', 'Zari Weaving', 45.0)
        """)
        cur.execute("""
            INSERT INTO artisans (first_name, last_name, phone, email, experience_years, skill_level, specialization, base_wage_rate)
            VALUES ('Meera', 'Sharma', '555-0102', 'meera@example.com', 8, 'Intermediate', 'Silk Dyeing', 30.0)
        """)
        # 3. Looms
        cur.execute("""
            INSERT INTO looms (loom_type, installation_date)
            VALUES ('Pit Loom', DATE('now'))
        """)
        cur.execute("""
            INSERT INTO looms (loom_type, installation_date)
            VALUES ('Powerloom', DATE('now'))
        """)
        # 4. Designs
        cur.execute("""
            INSERT INTO designs (design_name, regional_origin, complexity_multiplier, estimated_production_days, cultural_significance, eco_score)
            VALUES ('Banarasi Gold', 'Varanasi', 2.5, 30, 'Royal ceremonial wear', 85)
        """)
        cur.execute("""
            INSERT INTO designs (design_name, regional_origin, complexity_multiplier, estimated_production_days, cultural_significance, eco_score)
            VALUES ('Kanchipuram Silk', 'Tamil Nadu', 2.0, 25, 'Traditional wedding drape', 78)
        """)
        # 5. Raw Materials
        cur.execute("""
            INSERT INTO raw_materials (material_name, material_type, dye_type, unit_of_measure, stock_quantity, reorder_level, cost_per_unit, quality_grade, eco_friendly)
            VALUES ('Silk Yarn', 'Yarn', 'None', 'kg', 5000, 1000, 20.0, 'Premium', 0)
        """)
        cur.execute("""
            INSERT INTO raw_materials (material_name, material_type, dye_type, unit_of_measure, stock_quantity, reorder_level, cost_per_unit, quality_grade, eco_friendly)
            VALUES ('Natural Indigo Dye', 'Dye', 'Natural', 'liter', 200, 50, 15.0, 'Standard', 1)
        """)
        cur.execute("""
            INSERT INTO raw_materials (material_name, material_type, dye_type, unit_of_measure, stock_quantity, reorder_level, cost_per_unit, quality_grade, eco_friendly)
            VALUES ('Gold Zari Thread', 'Zari', 'None', 'kg', 300, 50, 120.0, 'Premium', 0)
        """)
        # 6. Suppliers
        cur.execute("""
            INSERT INTO suppliers (supplier_name, contact_person, phone, email, address)
            VALUES ('SilkCo', 'Anita', '0987654321', 'contact@silkco.com', '123 Silk St')
        """)
        # 7. Supplier-Material link
        cur.execute("""
            INSERT OR IGNORE INTO supplier_materials (supplier_id, material_id, supply_lead_time_days, unit_price)
            VALUES (1, 1, 7, 22.0)
        """)
        cur.execute("""
            INSERT OR IGNORE INTO supplier_materials (supplier_id, material_id, supply_lead_time_days, unit_price)
            VALUES (1, 2, 5, 16.0)
        """)
        # 8. Customers
        cur.execute("""
            INSERT INTO customers (company_name, contact_name, email, phone, billing_address, shipping_address)
            VALUES ('Heritage Boutique', 'Anita Rao', 'anita@royalboutique.com', '555-0201', '123 Palace Rd, Delhi', '123 Palace Rd, Delhi')
        """)
        # 9. Customer Orders and Order Items
        cur.execute("""
            INSERT INTO customer_orders (customer_id, order_date, required_delivery_date, status, total_amount)
            VALUES (1, DATE('now'), DATE('now','+30 day'), 'Pending', 0.0)
        """)
        order_id = cur.lastrowid
        cur.execute("""
            INSERT INTO order_items (order_id, design_id, quantity_meters, unit_price)
            VALUES (?, 1, 50, 1500)
        """, (order_id,))
        cur.execute("""
            INSERT INTO order_items (order_id, design_id, quantity_meters, unit_price)
            VALUES (?, 2, 30, 1800)
        """, (order_id,))
        # Update total_amount based on items
        cur.execute("""
            UPDATE customer_orders SET total_amount = (
                SELECT SUM(quantity_meters * unit_price) FROM order_items WHERE order_id = ?
            ) WHERE order_id = ?
        """, (order_id, order_id))
        # 10. Production Batch (scheduled)
        cur.execute("""
            INSERT INTO production_batches (design_id, artisan_id, loom_id, start_date, target_completion_date, quantity_meters, status)
            VALUES (1, 1, 1, DATE('now'), DATE('now','+35 day'), 50, 'Scheduled')
        """)
        batch_id = cur.lastrowid
        # 11. Batch Material Usage
        cur.execute("""
            INSERT INTO batch_material_usage (batch_id, material_id, quantity_used)
            VALUES (?, 1, 100)
        """, (batch_id,))
        cur.execute("""
            INSERT INTO batch_material_usage (batch_id, material_id, quantity_used)
            VALUES (?, 3, 5)
        """, (batch_id,))
        # 12. Shipment (set date fields)
        cur.execute("""
            INSERT INTO shipments (order_id, carrier_name, tracking_number, shipment_date, estimated_delivery_date, status)
            VALUES (?,?, 'TRK-2026-0001', DATE('now'), DATE('now','+5 day'), 'In Transit')
        """, (order_id, 'Heritage Couriers'))
        conn.commit()
        print('Sample data inserted successfully.')
    except sqlite3.Error as e:
        conn.rollback()
        print('Error inserting sample data:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    insert_sample_data()

import sqlite3
import os
import sys

# Define relative paths
DB_PATH = os.path.join("database", "heritage_tracker.db")
SCHEMA_PATH = os.path.join("database", "schema.sql")

def print_table(title, headers, rows):
    """
    Prints a beautifully aligned table to the console without external dependencies.
    """
    print(f"\n=== \033[1;36m{title}\033[0m ===")
    if not rows:
        print("\033[1;30m(No records found)\033[0m")
        return
    
    # Find max width for each column
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            val_str = str(val) if val is not None else "NULL"
            col_widths[i] = max(col_widths[i], len(val_str))
            
    # Format strings
    header_format = " | ".join([f"\033[1;37m{{:<{w}}}\033[0m" for w in col_widths])
    row_format = " | ".join([f"{{:<{w}}}" for w in col_widths])
    divider = "-+-".join(["-" * w for w in col_widths])
    
    # Print headers and data
    print(header_format.format(*headers))
    print(divider)
    for row in rows:
        str_row = [str(val) if val is not None else "NULL" for val in row]
        print(row_format.format(*str_row))
    print()

def main():
    print("\033[1;32mStarting Heritage Textile Tracker Simulation & Validation...\033[0m")
    
    # Check if database directory exists, create if not
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"Created database directory: {db_dir}")

    # Establish connection
    try:
        conn = sqlite3.connect(DB_PATH)
        # Enable Foreign Key enforcement in SQLite connection
        conn.execute("PRAGMA foreign_keys = ON;")
        print("Connected to SQLite database successfully. Foreign Keys Enabled.")
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        sys.exit(1)

    # 1. Initialize schema
    print("\nReading schema DDL from schema.sql...")
    if not os.path.exists(SCHEMA_PATH):
        print(f"Error: schema.sql file not found at {SCHEMA_PATH}")
        sys.exit(1)
        
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_ddl = f.read()
        conn.executescript(schema_ddl)
        conn.commit()
        print("\033[1;32mDatabase schema loaded successfully!\033[0m")
    except sqlite3.Error as e:
        print(f"\033[1;31mError during schema initialization:\033[0m\n{e}")
        conn.close()
        sys.exit(1)

    # 2. Insert Seed Data
    print("\nSeeding core database tables with initial records...")
    cursor = conn.cursor()
    
    try:
        # Users
        users = [
            ("admin_user", "pbkdf2_sha256$placeholder$admin", "Aravind Swamy", "admin@heritagetextile.org", "Admin"),
            ("inv_mgr", "pbkdf2_sha256$placeholder$inv", "Sanjay Dutt", "sanjay@heritagetextile.org", "Inventory Manager"),
            ("qc_inspect", "pbkdf2_sha256$placeholder$qc", "Kiran Rao", "kiran@heritagetextile.org", "QC Inspector"),
            ("fin_mgr", "pbkdf2_sha256$placeholder$fin", "Nisha Patel", "nisha@heritagetextile.org", "Finance Manager")
        ]
        cursor.executemany("""
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, ?)
        """, users)
        
        # Artisans
        artisans = [
            ("Ramesh", "Kumar", "9876543201", "ramesh.kumar@handloom.org", 12, "Master", "Banarasi Brocade", 450.0),
            ("Sita", "Devi", "9876543202", "sita.devi@handloom.org", 8, "Intermediate", "Kanjeevaram Silk", 350.0),
            ("Abdul", "Rahim", "9876543203", "abdul.rahim@handloom.org", 4, "Beginner", "Pochampally Ikat", 250.0)
        ]
        cursor.executemany("""
            INSERT INTO artisans (first_name, last_name, phone, email, experience_years, skill_level, specialization, base_wage_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, artisans)

        # Looms
        looms = [
            ("Pit Loom", "2024-01-15", "2026-03-10", 90, 95.0, "Available"),
            ("Frame Loom", "2025-05-20", "2026-04-12", 90, 90.0, "Available"),
            ("Jacquard Loom", "2023-08-25", "2026-02-18", 60, 98.0, "Available")
        ]
        cursor.executemany("""
            INSERT INTO looms (loom_type, installation_date, last_maintenance_date, maintenance_interval_days, efficiency_rating, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, looms)

        # Designs
        designs = [
            ("Royal Taj Brocade", "Varanasi", 2.5, 20, "Intricate gold zari Mughal floral bootis on pure silk.", 85),
            ("Golden Peacock Pallu", "Kanchipuram", 2.0, 15, "Traditional twin peacock motifs in pure gold thread.", 90),
            ("Geometric Ikat Wave", "Pochampally", 1.5, 10, "Double-ikat warp and weft geometric wave patterns.", 95)
        ]
        cursor.executemany("""
            INSERT INTO designs (design_name, regional_origin, complexity_multiplier, estimated_production_days, cultural_significance, eco_score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, designs)

        # Raw Materials
        materials = [
            ("Premium Mulberry Silk Yarn", "Yarn", "None", "kg", 50.0, 10.0, 2500.0, "Premium", 1),
            ("Crimson Natural Madder Dye", "Dye", "Natural", "kg", 15.0, 5.0, 1200.0, "Premium", 1),
            ("Golden Metallic Zari Thread", "Zari", "None", "kg", 8.0, 2.0, 5000.0, "Premium", 0),
            ("Indigo Natural Dye Powder", "Dye", "Natural", "kg", 3.0, 4.0, 900.0, "Standard", 1)  # Low stock initially (3.0 <= 4.0 reorder level)
        ]
        cursor.executemany("""
            INSERT INTO raw_materials (material_name, material_type, dye_type, unit_of_measure, stock_quantity, reorder_level, cost_per_unit, quality_grade, eco_friendly)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, materials)

        # Suppliers
        suppliers = [
            ("Varanasi Silk Syndicate", "Sunil Gupta", "9876543210", "sunil@varsilk.com", "Chowk, Varanasi", 4.5),
            ("Kanchi Thread Co.", "Meenakshi R.", "9876543211", "contact@kanchithread.com", "Temple Rd, Kanchipuram", 4.2)
        ]
        cursor.executemany("""
            INSERT INTO suppliers (supplier_name, contact_person, phone, email, address, sustainability_rating)
            VALUES (?, ?, ?, ?, ?, ?)
        """, suppliers)

        # Supplier Materials Linkage
        supplier_materials = [
            (1, 1, 5, 2400.0), # Varanasi supplies Mulberry Silk
            (1, 3, 7, 4800.0), # Varanasi supplies Golden Zari
            (2, 2, 4, 1150.0), # Kanchi supplies Madder Dye
            (2, 4, 3, 850.0)   # Kanchi supplies Indigo Dye
        ]
        cursor.executemany("""
            INSERT INTO supplier_materials (supplier_id, material_id, supply_lead_time_days, unit_price)
            VALUES (?, ?, ?, ?)
        """, supplier_materials)
        
        conn.commit()
        print("Core database tables seeded successfully.")
    except sqlite3.Error as e:
        print(f"\033[1;31mError during database seeding:\033[0m\n{e}")
        conn.close()
        sys.exit(1)

    # 3. Simulate Supply Chain Business Workflow
    print("\n-------------------------------------------------------------")
    print("SIMULATING SUPPLY CHAIN LIFECYCLE WORKFLOW (Trigger Executions)")
    print("-------------------------------------------------------------")

    try:
        # STEP 3.1: Create Customer and Customer Order
        print("\n[Step 1] Customer places an order...")
        cursor.execute("""
            INSERT INTO customers (company_name, contact_name, email, phone, billing_address, shipping_address)
            VALUES ('Nirvana Handloom Boutique', 'Ananya Sen', 'buyer@nirvanahandloom.com', '9812345678', 'MG Road, Bangalore', 'Koramangala, Bangalore')
        """)
        customer_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO customer_orders (customer_id, order_date, required_delivery_date, status, total_amount)
            VALUES (?, '2026-05-20', '2026-06-25', 'Pending', 75000.0)
        """, (customer_id,))
        order_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO order_items (order_id, design_id, quantity_meters, unit_price)
            VALUES (?, 1, 15.0, 5000.0) -- 15m of Royal Taj Brocade
        """, (order_id,))
        print(f"Customer Order #{order_id} created with Order Item details.")

        # STEP 3.2: Schedule Production Batches
        print("\n[Step 2] Scheduling Production Batches to fulfill the order...")
        # Batch 1 (Assigned to Artisan 1 - Ramesh Kumar, Loom 3, Design 1)
        cursor.execute("""
            INSERT INTO production_batches (design_id, artisan_id, loom_id, start_date, target_completion_date, quantity_meters, status)
            VALUES (1, 1, 3, '2026-05-21', '2026-06-12', 15.0, 'Scheduled')
        """)
        batch1_id = cursor.lastrowid
        
        # Batch 2 (Assigned to Artisan 2 - Sita Devi, Loom 2, Design 2 - 10 meters)
        cursor.execute("""
            INSERT INTO production_batches (design_id, artisan_id, loom_id, start_date, target_completion_date, quantity_meters, status)
            VALUES (2, 2, 2, '2026-05-20', '2026-06-04', 10.0, 'Scheduled')
        """)
        batch2_id = cursor.lastrowid

        # Associate raw materials needed for production run
        # Batch 1 uses: 10kg Silk, 2kg Madder Dye, 1.5kg Golden Zari
        batch1_materials = [
            (batch1_id, 1, 10.0),
            (batch1_id, 2, 2.0),
            (batch1_id, 3, 1.5)
        ]
        # Batch 2 uses: 6kg Silk, 1.2kg Madder Dye
        batch2_materials = [
            (batch2_id, 1, 6.0),
            (batch2_id, 2, 1.2)
        ]
        
        cursor.executemany("INSERT INTO batch_material_usage (batch_id, material_id, quantity_used) VALUES (?, ?, ?)", batch1_materials)
        cursor.executemany("INSERT INTO batch_material_usage (batch_id, material_id, quantity_used) VALUES (?, ?, ?)", batch2_materials)
        print(f"Production Batches Scheduled: Batch #{batch1_id} (15m Royal Taj) & Batch #{batch2_id} (10m Golden Peacock). Material usage defined.")

        # STEP 3.3: Start Production & Deduct Inventory (Trigger 1)
        print("\n[Step 3] Moving Production Batch #1 to 'In Progress'...")
        
        # Show Silk stock before
        cursor.execute("SELECT material_name, stock_quantity, reorder_level FROM raw_materials WHERE material_id = 1")
        silk_before = cursor.fetchone()
        print(f"Inventory Before: {silk_before[0]} = {silk_before[1]} {silk_before[2]} kg")

        # Update batch status to 'In Progress' to fire tg_deduct_inventory_on_batch_start
        cursor.execute("UPDATE production_batches SET status = 'In Progress' WHERE batch_id = ?", (batch1_id,))
        
        # Show Silk stock after
        cursor.execute("SELECT material_name, stock_quantity, reorder_level FROM raw_materials WHERE material_id = 1")
        silk_after = cursor.fetchone()
        print(f"Inventory After Start (Trigger 1 Deducts Stock): {silk_after[0]} = {silk_after[1]} kg (Deducted 10.0 kg)")

        # Move Batch 2 to 'In Progress' as well
        cursor.execute("UPDATE production_batches SET status = 'In Progress' WHERE batch_id = ?", (batch2_id,))

        # STEP 3.4: Low Stock Alert Trigger Test (Trigger 2)
        print("\n[Step 4] Simulating Indigo Dye stock check update...")
        # Indigo powder starts at 3.0 kg, which is <= 4.0 kg reorder level. An update triggers alert registration.
        cursor.execute("UPDATE raw_materials SET stock_quantity = 2.5 WHERE material_id = 4")
        
        cursor.execute("""
            SELECT al.alert_id, rm.material_name, al.alert_date, al.current_stock, al.reorder_level, al.status 
            FROM inventory_alerts al
            JOIN raw_materials rm ON al.material_id = rm.material_id
        """)
        alerts = cursor.fetchall()
        print_table("INVENTORY ALERTS LOGGED (Trigger 2)", 
                    ["Alert ID", "Material Name", "Alert Date", "Current Stock", "Reorder Level", "Alert Status"], 
                    alerts)

        # STEP 3.5: Log Production Delays
        print("\n[Step 5] Logging production delay due to loom maintenance issues...")
        cursor.execute("""
            INSERT INTO production_delays (batch_id, reason_category, description, start_date, resolved_date)
            VALUES (?, 'Loom Breakdown', 'Jacquard electronic cards loose contact. Maintenance called.', '2026-05-24', '2026-05-26')
        """, (batch1_id,))
        print("Loom breakdown logged and resolved on 2026-05-26.")

        # STEP 3.6: Batch Completion, Wage Calculation (Trigger 3) and Authenticity Record (Trigger 4)
        print("\n[Step 6] Batch #1 completed. Logging completion and checking auto-actions...")
        cursor.execute("""
            UPDATE production_batches 
            SET status = 'Completed', actual_completion_date = '2026-06-08' 
            WHERE batch_id = ?
        """, (batch1_id,))
        
        # Verify Wages generated
        cursor.execute("""
            SELECT wp.payment_id, a.first_name || ' ' || a.last_name, wp.calculated_wage, wp.net_wage, wp.payment_status 
            FROM wage_payments wp
            JOIN artisans a ON wp.artisan_id = a.artisan_id
            WHERE wp.batch_id = ?
        """, (batch1_id,))
        wage1 = cursor.fetchall()
        print_table("AUTO-CALCULATED ARTISAN WAGE (Trigger 3)",
                    ["Payment ID", "Artisan Name", "Gross Wage (Calculated)", "Net Wage", "Payment Status"],
                    wage1)

        # Verify Authenticity Certificate created
        cursor.execute("""
            SELECT verification_code, batch_id, qr_code_url, generation_date, blockchain_hash 
            FROM authenticity_records 
            WHERE batch_id = ?
        """, (batch1_id,))
        auth1 = cursor.fetchall()
        print_table("AUTO-GENERATED AUTHENTICITY CERTIFICATE (Trigger 4)",
                    ["Verification Code", "Batch ID", "QR Code Verification Link", "Issue Date", "Blockchain Ledger Hash"],
                    auth1)

        # Complete Batch 2 as well to demonstrate QC fail and Rework
        cursor.execute("""
            UPDATE production_batches 
            SET status = 'Completed', actual_completion_date = '2026-06-05' 
            WHERE batch_id = ?
        """, (batch2_id,))

        # STEP 3.7: Quality Control Inspection, Bonuses & Deductions, Rework Logging (Trigger 5)
        print("\n[Step 7] Running QC Inspections on finished batches...")
        
        # Batch 1 gets an excellent score of 97.0 (triggers a 10% bonus)
        cursor.execute("""
            INSERT INTO inspections (batch_id, inspector_id, inspection_date, quality_score, status, defects_found)
            VALUES (?, 3, '2026-06-09', 97.0, 'Passed', 'Flawless weave tension, vibrant eco-friendly natural dye.')
        """, (batch1_id,))
        
        # Batch 2 fails inspection due to weft defects, status 'Rework Required' (triggers 15% penalty & rework assignment)
        cursor.execute("""
            INSERT INTO inspections (batch_id, inspector_id, inspection_date, quality_score, status, defects_found)
            VALUES (?, 3, '2026-06-06', 72.0, 'Rework Required', 'Warp tension issues in center panel causing minor gaps.')
        """, (batch2_id,))

        # Print wage adjustments to show bonus and deduction
        cursor.execute("""
            SELECT wp.payment_id, a.first_name || ' ' || a.last_name, wp.calculated_wage, wp.bonus_applied, wp.deductions, wp.net_wage, wp.payment_status 
            FROM wage_payments wp
            JOIN artisans a ON wp.artisan_id = a.artisan_id
        """)
        wages_adjusted = cursor.fetchall()
        print_table("ARTISAN WAGES AFTER QC ADJUSTMENTS (Trigger 5 Bonus/Penalty)",
                    ["Payment ID", "Artisan Name", "Gross Base Wage", "QC Bonus (+10%)", "QC Deduction (-15%)", "Net Adjusted Wage", "Payment Status"],
                    wages_adjusted)

        # Print automatic rework assignment
        cursor.execute("""
            SELECT rl.rework_id, rl.inspection_id, a.first_name || ' ' || a.last_name, rl.defect_type, rl.rework_instructions, rl.status
            FROM rework_logs rl
            JOIN artisans a ON rl.assigned_artisan_id = a.artisan_id
        """)
        rework_assigned = cursor.fetchall()
        print_table("AUTO-ASSIGNED REWORK ASSIGNMENT (Trigger 5 Loop)",
                    ["Rework ID", "Insp. ID", "Assigned Artisan", "Defect Type", "Rework Instructions", "Rework Status"],
                    rework_assigned)

        # STEP 3.8: Dispatch Shipment
        print("\n[Step 8] Shipping verified goods to Customer...")
        cursor.execute("UPDATE customer_orders SET status = 'Processing' WHERE order_id = ?", (order_id,))
        
        cursor.execute("""
            INSERT INTO shipments (order_id, carrier_name, tracking_number, shipment_date, estimated_delivery_date, status)
            VALUES (?, 'Heritage Express Logistics', 'HTX-908234671-IN', '2026-06-10', '2026-06-14', 'In Transit')
        """, (order_id,))
        
        cursor.execute("UPDATE customer_orders SET status = 'Shipped' WHERE order_id = ?", (order_id,))
        print("Shipment dispatched. Tracking registered. Customer order status updated to 'Shipped'.")

        conn.commit()
        print("\n\033[1;32mSupply Chain Workflow Simulation Completed Successfully!\033[0m")
    except sqlite3.Error as e:
        print(f"\033[1;31mError during workflow simulation:\033[0m\n{e}")
        conn.rollback()
        conn.close()
        sys.exit(1)

    # 4. Execute and Display Analytical Queries
    print("\n-------------------------------------------------------------")
    print("EXECUTING COMPLEX BUSINESS INTELLIGENCE ANALYTICAL QUERIES")
    print("-------------------------------------------------------------")

    try:
        # Query 1: Artisan Efficiency and Variance Analysis
        q1_headers = ["Artisan ID", "Artisan Name", "Design Name", "Completed Batches", "Avg Est Days", "Avg Act Days", "Days Variance"]
        cursor.execute("""
            SELECT 
                a.artisan_id,
                a.first_name || ' ' || a.last_name AS artisan_name,
                d.design_name,
                COUNT(b.batch_id) AS completed_batches,
                ROUND(AVG(d.estimated_production_days), 1) AS avg_estimated_days,
                ROUND(AVG(JULIANDAY(b.actual_completion_date) - JULIANDAY(b.start_date)), 1) AS avg_actual_days,
                ROUND(AVG((JULIANDAY(b.actual_completion_date) - JULIANDAY(b.start_date)) - d.estimated_production_days), 1) AS avg_days_variance
            FROM artisans a
            JOIN production_batches b ON a.artisan_id = b.artisan_id
            JOIN designs d ON b.design_id = d.design_id
            WHERE b.status = 'Completed'
            GROUP BY a.artisan_id, d.design_id
            ORDER BY avg_days_variance ASC;
        """)
        q1_results = cursor.fetchall()
        print_table("Query 1: Artisan Production Efficiency & Schedule Variance Analysis", q1_headers, q1_results)

        # Query 2: Supply Chain Delay and Bottleneck Analysis
        q2_headers = ["Delay Reason", "Incident Count", "Total Delay Days", "Avg Delay Days"]
        cursor.execute("""
            SELECT 
                pd.reason_category,
                COUNT(pd.delay_id) AS total_delay_incidents,
                SUM(CASE 
                    WHEN pd.resolved_date IS NOT NULL THEN (JULIANDAY(pd.resolved_date) - JULIANDAY(pd.start_date))
                    ELSE (JULIANDAY('now') - JULIANDAY(pd.start_date))
                END) AS total_delay_days,
                ROUND(AVG(CASE 
                    WHEN pd.resolved_date IS NOT NULL THEN (JULIANDAY(pd.resolved_date) - JULIANDAY(pd.start_date))
                    ELSE (JULIANDAY('now') - JULIANDAY(pd.start_date))
                END), 1) AS avg_delay_duration_days
            FROM production_delays pd
            GROUP BY pd.reason_category
            ORDER BY total_delay_days DESC;
        """)
        q2_results = cursor.fetchall()
        print_table("Query 2: Supply Chain Delay & Production Bottleneck Analysis", q2_headers, q2_results)

        # Query 3: Authenticity & Heritage Story Query (QR Code Lookup)
        # Fetching code for batch 1 to display story
        cursor.execute("SELECT verification_code FROM authenticity_records WHERE batch_id = 1")
        verification_code = cursor.fetchone()[0]
        
        q3_headers = ["Verification Code", "Motif Name", "Regional Origin", "Cultural Significance", "Master Artisan", "Artisan Experience", "Weaving Loom", "Completion Date", "Quality Certified", "Raw Materials Used", "Blockchain Hash"]
        cursor.execute("""
            SELECT 
                ar.verification_code,
                d.design_name AS motif_name,
                d.regional_origin,
                d.cultural_significance,
                a.first_name || ' ' || a.last_name AS master_artisan,
                a.experience_years || ' years' AS artisan_experience,
                l.loom_type AS weaving_loom,
                b.actual_completion_date AS completion_date,
                i.quality_score AS certified_quality,
                GROUP_CONCAT(rm.material_name || ' (' || rm.dye_type || ' Dye)', ', ') AS raw_materials_used,
                ar.blockchain_hash AS authenticity_proof
            FROM authenticity_records ar
            JOIN production_batches b ON ar.batch_id = b.batch_id
            JOIN designs d ON b.design_id = d.design_id
            JOIN artisans a ON b.artisan_id = a.artisan_id
            JOIN looms l ON b.loom_id = l.loom_id
            LEFT JOIN inspections i ON b.batch_id = i.batch_id AND i.status = 'Passed'
            LEFT JOIN batch_material_usage bmu ON b.batch_id = bmu.batch_id
            LEFT JOIN raw_materials rm ON bmu.material_id = rm.material_id
            WHERE ar.verification_code = ?
            GROUP BY ar.verification_code;
        """, (verification_code,))
        q3_results = cursor.fetchall()
        # Pivot query 3 results for visual clarity since it contains many columns
        print(f"\n=== \033[1;36mQuery 3: Authenticity Heritage Pedigree Story (Lookup: {verification_code})\033[0m ===")
        if q3_results:
            story = q3_results[0]
            for head, val in zip(q3_headers, story):
                print(f"\033[1;37m{head:<25}\033[0m: {val}")
        print()

        # Query 4: Financial Ledger & Profitability Analysis
        q4_headers = ["Batch ID", "Design Name", "Qty (m)", "Material Cost", "Labor Cost", "Total Cost", "Est. Revenue", "Net Profit"]
        cursor.execute("""
            SELECT 
                b.batch_id,
                d.design_name,
                b.quantity_meters AS quantity_meters_produced,
                ROUND(COALESCE(SUM(bmu.quantity_used * rm.cost_per_unit), 0.0), 2) AS material_cost,
                ROUND(wp.net_wage, 2) AS labor_cost,
                ROUND(COALESCE(SUM(bmu.quantity_used * rm.cost_per_unit), 0.0) + wp.net_wage, 2) AS total_production_cost,
                ROUND(b.quantity_meters * COALESCE((
                    SELECT AVG(unit_price) 
                    FROM order_items 
                    WHERE design_id = d.design_id
                ), d.complexity_multiplier * 1500.0), 2) AS estimated_revenue,
                ROUND((b.quantity_meters * COALESCE((
                    SELECT AVG(unit_price) 
                    FROM order_items 
                    WHERE design_id = d.design_id
                ), d.complexity_multiplier * 1500.0)) - (COALESCE(SUM(bmu.quantity_used * rm.cost_per_unit), 0.0) + wp.net_wage), 2) AS net_profit
            FROM production_batches b
            JOIN designs d ON b.design_id = d.design_id
            LEFT JOIN batch_material_usage bmu ON b.batch_id = bmu.batch_id
            LEFT JOIN raw_materials rm ON bmu.material_id = rm.material_id
            LEFT JOIN wage_payments wp ON b.batch_id = wp.batch_id
            WHERE b.status = 'Completed'
            GROUP BY b.batch_id;
        """)
        q4_results = cursor.fetchall()
        print_table("Query 4: Relational Ledger & Net Profitability Analysis", q4_headers, q4_results)

    except sqlite3.Error as e:
        print(f"\033[1;31mError executing analytical queries:\033[0m\n{e}")
        conn.close()
        sys.exit(1)

    # 5. Display Dashboard Views
    print("\n-------------------------------------------------------------")
    print("DISPLAYING DATABASE VIEWS (Dashboard Reporting Layer)")
    print("-------------------------------------------------------------")

    try:
        # View 1: Artisan Performance Dashboard
        cursor.execute("SELECT * FROM vw_artisan_performance")
        v1_rows = cursor.fetchall()
        print_table("View 1: vw_artisan_performance", 
                    ["Artisan ID", "Name", "Exp. Years", "Skill Level", "Specialization", "Batches", "Total Output (m)", "Avg QC Score", "Total Wages Earned", "Delays"], 
                    v1_rows)

        # View 2: Environmental Sustainability & Eco-Metrics
        cursor.execute("SELECT * FROM vw_sustainability_metrics")
        v2_rows = cursor.fetchall()
        print_table("View 2: vw_sustainability_metrics", 
                    ["Batches", "Avg Eco Score", "Eco-Friendly Material (kg)", "Total Material (kg)", "Eco Material %", "Natural Dye Used (kg)", "Synthetic Dye Used (kg)", "Natural Dye Ratio %"], 
                    v2_rows)

        # View 3: Active Supply Chain & Production Status
        cursor.execute("SELECT * FROM vw_active_supply_chain")
        v3_rows = cursor.fetchall()
        print_table("View 3: vw_active_supply_chain", 
                    ["Batch ID", "Design Name", "Artisan", "Loom ID", "Loom Type", "Start Date", "Target Date", "Meters", "Prod Status", "Timeline Status", "Active Delays"], 
                    v3_rows)

        # View 4: Real-time Inventory Status & Alerts
        cursor.execute("SELECT * FROM vw_inventory_status")
        v4_rows = cursor.fetchall()
        print_table("View 4: vw_inventory_status", 
                    ["Material ID", "Material Name", "Type", "Quality", "Stock Qty", "Reorder Level", "Unit", "Stock Status", "Active Alert Date", "Supplier Name", "Supplier Phone", "Supplier Email"], 
                    v4_rows)

        # View 5: Customer Order Fulfillment Summary
        cursor.execute("SELECT * FROM vw_order_fulfillment_status")
        v5_rows = cursor.fetchall()
        print_table("View 5: vw_order_fulfillment_status", 
                    ["Order ID", "Customer Name", "Company", "Order Date", "Required Date", "Order Status", "Total Amt", "Unique Designs", "Total Meters", "Tracking Num", "Shipment Status"], 
                    v5_rows)

    except sqlite3.Error as e:
        print(f"\033[1;31mError reading database views:\033[0m\n{e}")
        conn.close()
        sys.exit(1)

    # Close connection
    conn.close()
    print("\033[1;32mHeritage Textile Tracker Simulation Completed successfully!\033[0m")

if __name__ == "__main__":
    main()

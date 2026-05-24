from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "heritage_secret_key_zari_brocade"
DB_PATH = os.path.join("database", "heritage_tracker.db")

def get_db_connection():
    """
    Establishes connection to the SQLite database.
    Enforces foreign key support and returns Row objects.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

# Helper function to check if user is logged in
def is_logged_in():
    return "user_id" in session

# ----------------------------------------------------------------------------
# PUBLIC ROUTES
# ----------------------------------------------------------------------------

@app.route("/")
def index():
    """
    Public landing page with heritage storytelling.
    """
    return render_template("index.html")

@app.route("/verify", methods=["GET", "POST"])
def verify():
    """
    Public Authenticity Verification Portal.
    """
    cert = None
    searched = False
    code = ""
    if request.method == "POST":
        code = request.form.get("verification_code", "").strip()
    elif request.args.get("code"):
        code = request.args.get("code").strip()
        
    if code:
        searched = True
        conn = get_db_connection()
        # Query 3: Authenticity Heritage Story Query (lookup by verification code)
        query = """
            SELECT 
                ar.verification_code,
                d.design_name AS motif_name,
                d.regional_origin,
                d.cultural_significance,
                a.first_name || ' ' || a.last_name AS master_artisan,
                a.experience_years,
                a.skill_level,
                l.loom_type AS weaving_loom,
                b.actual_completion_date AS completion_date,
                i.quality_score AS certified_quality,
                i.defects_found,
                GROUP_CONCAT(rm.material_name || ' (' || rm.dye_type || ' Dye)', ', ') AS raw_materials_used,
                ar.blockchain_hash AS authenticity_proof,
                ar.verification_count
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
        """
        cert = conn.execute(query, (code,)).fetchone()
        
        # Increment verification count if record found
        if cert:
            conn.execute("""
                UPDATE authenticity_records 
                SET verification_count = verification_count + 1 
                WHERE verification_code = ?
            """, (code,))
            conn.commit()
            
        conn.close()
        
    return render_template("verification.html", cert=cert, searched=searched, code=code)

# ----------------------------------------------------------------------------
# ADMIN LOGIN / LOGOUT
# ----------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Admin Login Page.
    """
    if is_logged_in():
        return redirect(url_for("dashboard"))
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND status = 'Active'", (username,)).fetchone()
        conn.close()
        
        if user:
            # Check password suffix
            expected_suffix = user["password_hash"].split("$")[-1]
            if password == expected_suffix:
                session["user_id"] = user["user_id"]
                session["username"] = user["username"]
                session["full_name"] = user["full_name"]
                session["role"] = user["role"]
                flash(f"Welcome back, {user['full_name']}!", "success")
                return redirect(url_for("dashboard"))
                
        flash("Invalid username or password.", "danger")
        
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))

# ----------------------------------------------------------------------------
# MANAGEMENT DASHBOARDS (Login Required)
# ----------------------------------------------------------------------------

@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    role = session.get("role")
    
    # Common KPI metrics (fetched for all roles that need them)
    artisans_count = conn.execute("SELECT COUNT(*) FROM artisans WHERE status = 'Active'").fetchone()[0]
    active_production = conn.execute("SELECT COUNT(*) FROM production_batches WHERE status IN ('In Progress', 'Scheduled', 'On Hold')").fetchone()[0]
    low_stock_alerts = conn.execute("SELECT COUNT(*) FROM inventory_alerts WHERE status = 'Active'").fetchone()[0]
    revenue = conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM customer_orders WHERE status != 'Cancelled'").fetchone()[0]
    shipments_count = conn.execute("SELECT COUNT(*) FROM shipments WHERE status = 'In Transit'").fetchone()[0]
    qc_metrics = conn.execute("SELECT COALESCE(ROUND(AVG(quality_score), 1), 0.0) FROM inspections").fetchone()[0]
    
    # Role-specific KPIs
    materials_count = 0
    pending_inspections = 0
    pending_wages = 0
    total_orders = 0
    
    if role == 'Inventory Manager':
        materials_count = conn.execute("SELECT COUNT(*) FROM raw_materials").fetchone()[0]
    elif role == 'QC Inspector':
        pending_inspections = conn.execute("""
            SELECT COUNT(*) FROM production_batches 
            WHERE status = 'Completed' AND batch_id NOT IN (SELECT batch_id FROM inspections)
        """).fetchone()[0]
    elif role == 'Finance Manager':
        pending_wages = conn.execute("SELECT COUNT(*) FROM wage_payments WHERE payment_status = 'Pending'").fetchone()[0]
        total_orders = conn.execute("SELECT COUNT(*) FROM customer_orders").fetchone()[0]
    
    # Alert list
    alerts_list = conn.execute("SELECT * FROM vw_inventory_status WHERE stock_status IN ('Low Stock', 'Out of Stock') LIMIT 5").fetchall()
    
    # Active production list
    active_batches = conn.execute("SELECT * FROM vw_active_supply_chain LIMIT 5").fetchall()
    
    conn.close()
    
    return render_template(
        "dashboard.html",
        artisans_count=artisans_count,
        active_production=active_production,
        low_stock_alerts=low_stock_alerts,
        revenue=revenue,
        shipments_count=shipments_count,
        qc_metrics=qc_metrics,
        materials_count=materials_count,
        pending_inspections=pending_inspections,
        pending_wages=pending_wages,
        total_orders=total_orders,
        alerts_list=alerts_list,
        active_batches=active_batches
    )

@app.route("/artisans", methods=["GET", "POST"])
def artisans():
    if not is_logged_in():
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    
    if request.method == "POST":
        # Check permissions (only Admin or Finance Manager can add artisans)
        if session.get("role") not in ["Admin", "Finance Manager"]:
            flash("Unauthorized action.", "danger")
            return redirect(url_for("artisans"))
            
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        experience = request.form.get("experience_years")
        skill_level = request.form.get("skill_level")
        specialization = request.form.get("specialization")
        base_wage = request.form.get("base_wage_rate")
        certifications = request.form.get("certification_details")
        
        try:
            conn.execute("""
                INSERT INTO artisans (first_name, last_name, phone, email, experience_years, skill_level, specialization, base_wage_rate, certification_details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, phone, email, experience, skill_level, specialization, base_wage, certifications))
            conn.commit()
            flash("Artisan registered successfully!", "success")
        except sqlite3.Error as e:
            conn.rollback()
            flash(f"Error registering artisan: {e}", "danger")
            
        return redirect(url_for("artisans"))
        
    artisans_list = conn.execute("SELECT * FROM vw_artisan_performance").fetchall()
    conn.close()
    return render_template("artisans.html", artisans_list=artisans_list)

@app.route("/inventory", methods=["GET", "POST"])
def inventory():
    if not is_logged_in():
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    
    if request.method == "POST":
        # Check permissions (Admin or Inventory Manager)
        if session.get("role") not in ["Admin", "Inventory Manager"]:
            flash("Unauthorized action.", "danger")
            return redirect(url_for("inventory"))
            
        material_id = request.form.get("material_id")
        quantity = request.form.get("quantity")
        
        try:
            # Trigger tg_check_inventory_alert will fire if quantity <= reorder_level
            conn.execute("UPDATE raw_materials SET stock_quantity = ? WHERE material_id = ?", (quantity, material_id))
            conn.commit()
            flash("Material stock updated successfully!", "success")
        except sqlite3.Error as e:
            conn.rollback()
            flash(f"Error updating stock: {e}", "danger")
            
        return redirect(url_for("inventory"))
        
    inventory_list = conn.execute("SELECT * FROM vw_inventory_status").fetchall()
    materials_select = conn.execute("SELECT material_id, material_name FROM raw_materials").fetchall()
    conn.close()
    return render_template("inventory.html", inventory_list=inventory_list, materials_select=materials_select)

@app.route("/production", methods=["GET", "POST"])
def production():
    if not is_logged_in():
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    
    if request.method == "POST":
        # Check permissions (Admin or Inventory Manager)
        if session.get("role") not in ["Admin", "Inventory Manager"]:
            flash("Unauthorized action.", "danger")
            return redirect(url_for("production"))
            
        action = request.form.get("action")
        
        if action == "schedule":
            design_id = request.form.get("design_id")
            artisan_id = request.form.get("artisan_id")
            loom_id = request.form.get("loom_id")
            start_date = request.form.get("start_date")
            target_date = request.form.get("target_completion_date")
            quantity = request.form.get("quantity_meters")
            
            # Materials inputs
            mat1_id = request.form.get("material1_id")
            mat1_qty = request.form.get("material1_qty")
            mat2_id = request.form.get("material2_id")
            mat2_qty = request.form.get("material2_qty")
            
            try:
                # Insert Batch
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO production_batches (design_id, artisan_id, loom_id, start_date, target_completion_date, quantity_meters, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'Scheduled')
                """, (design_id, artisan_id, loom_id, start_date, target_date, quantity))
                batch_id = cursor.lastrowid
                
                # Insert Material Usages
                if mat1_id and mat1_qty:
                    cursor.execute("INSERT INTO batch_material_usage (batch_id, material_id, quantity_used) VALUES (?, ?, ?)", (batch_id, mat1_id, mat1_qty))
                if mat2_id and mat2_qty:
                    cursor.execute("INSERT INTO batch_material_usage (batch_id, material_id, quantity_used) VALUES (?, ?, ?)", (batch_id, mat2_id, mat2_qty))
                    
                conn.commit()
                flash(f"Production Batch #{batch_id} scheduled and materials linked successfully!", "success")
            except sqlite3.Error as e:
                conn.rollback()
                flash(f"Error scheduling batch: {e}", "danger")
                
        elif action == "start":
            batch_id = request.form.get("batch_id")
            try:
                # Trigger tg_deduct_inventory_on_batch_start fires
                conn.execute("UPDATE production_batches SET status = 'In Progress' WHERE batch_id = ?", (batch_id,))
                conn.commit()
                flash(f"Batch #{batch_id} status updated to In Progress. Raw materials deducted.", "success")
            except sqlite3.Error as e:
                conn.rollback()
                flash(f"Error starting batch: {e}", "danger")
                
        elif action == "complete":
            batch_id = request.form.get("batch_id")
            try:
                # Trigger tg_calculate_wage_on_completion & tg_generate_authenticity_record fire
                conn.execute("""
                    UPDATE production_batches 
                    SET status = 'Completed', actual_completion_date = STRFTIME('%Y-%m-%d', 'now') 
                    WHERE batch_id = ?
                """, (batch_id,))
                conn.commit()
                flash(f"Batch #{batch_id} marked Completed. Wage record and Authenticity Certificate generated!", "success")
            except sqlite3.Error as e:
                conn.rollback()
                flash(f"Error completing batch: {e}", "danger")
                
        elif action == "delay":
            batch_id = request.form.get("batch_id")
            category = request.form.get("reason_category")
            desc = request.form.get("description")
            start_date = request.form.get("delay_start_date")
            
            try:
                conn.execute("""
                    INSERT INTO production_delays (batch_id, reason_category, description, start_date)
                    VALUES (?, ?, ?, ?)
                """, (batch_id, category, desc, start_date))
                conn.execute("UPDATE production_batches SET status = 'On Hold' WHERE batch_id = ?", (batch_id,))
                conn.commit()
                flash("Delay event logged successfully. Batch set to On Hold.", "warning")
            except sqlite3.Error as e:
                conn.rollback()
                flash(f"Error logging delay: {e}", "danger")
                
        return redirect(url_for("production"))
        
    # Get lists
    batches = conn.execute("""
        SELECT b.*, d.design_name, a.first_name || ' ' || a.last_name as artisan_name, l.loom_type 
        FROM production_batches b 
        JOIN designs d ON b.design_id = d.design_id 
        JOIN artisans a ON b.artisan_id = a.artisan_id 
        JOIN looms l ON b.loom_id = l.loom_id
        ORDER BY b.batch_id DESC
    """).fetchall()
    
    # Active delays
    delays = conn.execute("""
        SELECT pd.*, d.design_name 
        FROM production_delays pd
        JOIN production_batches pb ON pd.batch_id = pb.batch_id
        JOIN designs d ON pb.design_id = d.design_id
        WHERE pd.resolved_date IS NULL
    """).fetchall()
    
    # Select dropdown lists
    designs_list = conn.execute("SELECT design_id, design_name FROM designs").fetchall()
    artisans_list = conn.execute("SELECT artisan_id, first_name || ' ' || last_name as name FROM artisans WHERE status='Active'").fetchall()
    looms_list = conn.execute("SELECT loom_id, loom_type FROM looms WHERE status='Available'").fetchall()
    materials_list = conn.execute("SELECT material_id, material_name FROM raw_materials").fetchall()
    
    conn.close()
    return render_template(
        "production.html",
        batches=batches,
        delays=delays,
        designs_list=designs_list,
        artisans_list=artisans_list,
        looms_list=looms_list,
        materials_list=materials_list
    )

@app.route("/qc", methods=["GET", "POST"])
def qc():
    if not is_logged_in():
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    
    if request.method == "POST":
        # Check permissions (Admin or QC Inspector)
        if session.get("role") not in ["Admin", "QC Inspector"]:
            flash("Unauthorized action.", "danger")
            return redirect(url_for("qc"))
            
        batch_id = request.form.get("batch_id")
        inspector_id = session.get("user_id")
        score = request.form.get("quality_score")
        status_ins = request.form.get("status")
        defects = request.form.get("defects_found")
        inspection_date = request.form.get("inspection_date")
        
        try:
            # Trigger tg_apply_qc_wage_adjustment adjustments will occur
            conn.execute("""
                INSERT INTO inspections (batch_id, inspector_id, inspection_date, quality_score, status, defects_found)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (batch_id, inspector_id, inspection_date, score, status_ins, defects))
            conn.commit()
            flash("Inspection logged successfully. Wage calculations adjusted.", "success")
        except sqlite3.Error as e:
            conn.rollback()
            flash(f"Error logging inspection: {e}", "danger")
            
        return redirect(url_for("qc"))
        
    inspections_list = conn.execute("""
        SELECT i.*, d.design_name, b.quantity_meters, u.full_name as inspector_name 
        FROM inspections i 
        JOIN production_batches b ON i.batch_id = b.batch_id 
        JOIN designs d ON b.design_id = d.design_id
        JOIN users u ON i.inspector_id = u.user_id
        ORDER BY i.inspection_id DESC
    """).fetchall()
    
    rework_list = conn.execute("""
        SELECT r.*, a.first_name || ' ' || a.last_name as artisan_name, i.quality_score, d.design_name
        FROM rework_logs r 
        JOIN artisans a ON r.assigned_artisan_id = a.artisan_id
        JOIN inspections i ON r.inspection_id = i.inspection_id
        JOIN production_batches b ON i.batch_id = b.batch_id
        JOIN designs d ON b.design_id = d.design_id
        ORDER BY r.rework_id DESC
    """).fetchall()
    
    completed_batches_select = conn.execute("""
        SELECT b.batch_id, d.design_name, b.quantity_meters 
        FROM production_batches b 
        JOIN designs d ON b.design_id = d.design_id
        WHERE b.status = 'Completed' AND b.batch_id NOT IN (SELECT batch_id FROM inspections)
    """).fetchall()
    
    conn.close()
    return render_template(
        "qc.html",
        inspections_list=inspections_list,
        rework_list=rework_list,
        completed_batches_select=completed_batches_select
    )

@app.route("/wages", methods=["GET", "POST"])
def wages():
    if not is_logged_in():
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    
    if request.method == "POST":
        # Check permissions (Admin or Finance Manager)
        if session.get("role") not in ["Admin", "Finance Manager"]:
            flash("Unauthorized action.", "danger")
            return redirect(url_for("wages"))
            
        payment_id = request.form.get("payment_id")
        
        try:
            conn.execute("UPDATE wage_payments SET payment_status = 'Paid' WHERE payment_id = ?", (payment_id,))
            conn.commit()
            flash("Wage payment processed successfully!", "success")
        except sqlite3.Error as e:
            conn.rollback()
            flash(f"Error processing wage payment: {e}", "danger")
            
        return redirect(url_for("wages"))
        
    wages_list = conn.execute("""
        SELECT wp.*, a.first_name || ' ' || a.last_name as artisan_name, d.design_name, b.quantity_meters 
        FROM wage_payments wp 
        JOIN artisans a ON wp.artisan_id = a.artisan_id 
        JOIN production_batches b ON wp.batch_id = b.batch_id 
        JOIN designs d ON b.design_id = d.design_id
        ORDER BY wp.payment_id DESC
    """).fetchall()
    
    conn.close()
    return render_template("wages.html", wages_list=wages_list)

@app.route("/orders", methods=["GET", "POST"])
def orders():
    if not is_logged_in():
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    
    if request.method == "POST":
        # Check permissions (Admin or Finance Manager)
        if session.get("role") not in ["Admin", "Finance Manager"]:
            flash("Unauthorized action.", "danger")
            return redirect(url_for("orders"))
            
        company_name = request.form.get("company_name")
        contact_name = request.form.get("contact_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("shipping_address")
        
        design_id = request.form.get("design_id")
        quantity = request.form.get("quantity")
        price = request.form.get("price")
        
        order_date = request.form.get("order_date")
        required_date = request.form.get("required_date")
        
        total = float(quantity) * float(price)
        
        try:
            cursor = conn.cursor()
            # Create customer or check if exists
            cursor.execute("SELECT customer_id FROM customers WHERE email = ?", (email,))
            cust_row = cursor.fetchone()
            if cust_row:
                cust_id = cust_row["customer_id"]
            else:
                cursor.execute("""
                    INSERT INTO customers (company_name, contact_name, email, phone, shipping_address)
                    VALUES (?, ?, ?, ?, ?)
                """, (company_name, contact_name, email, phone, address))
                cust_id = cursor.lastrowid
                
            # Create Order
            cursor.execute("""
                INSERT INTO customer_orders (customer_id, order_date, required_delivery_date, status, total_amount)
                VALUES (?, ?, ?, 'Pending', ?)
            """, (cust_id, order_date, required_date, total))
            order_id = cursor.lastrowid
            
            # Create Order Item
            cursor.execute("""
                INSERT INTO order_items (order_id, design_id, quantity_meters, unit_price)
                VALUES (?, ?, ?, ?)
            """, (order_id, design_id, quantity, price))
            
            conn.commit()
            flash(f"Order #{order_id} created successfully!", "success")
        except sqlite3.Error as e:
            conn.rollback()
            flash(f"Error creating order: {e}", "danger")
            
        return redirect(url_for("orders"))
        
    orders_list = conn.execute("SELECT * FROM vw_order_fulfillment_status ORDER BY order_id DESC").fetchall()
    designs_list = conn.execute("SELECT design_id, design_name FROM designs").fetchall()
    conn.close()
    return render_template("orders.html", orders_list=orders_list, designs_list=designs_list)

@app.route("/shipments", methods=["GET", "POST"])
def shipments():
    if not is_logged_in():
        return redirect(url_for("login"))
        
    conn = get_db_connection()
    
    if request.method == "POST":
        # Check permissions (Admin or Inventory Manager)
        if session.get("role") not in ["Admin", "Inventory Manager"]:
            flash("Unauthorized action.", "danger")
            return redirect(url_for("shipments"))
            
        action = request.form.get("action")
        
        if action == "create":
            order_id = request.form.get("order_id")
            carrier = request.form.get("carrier_name")
            tracking = request.form.get("tracking_number")
            ship_date = request.form.get("shipment_date")
            est_date = request.form.get("estimated_delivery_date")
            
            try:
                conn.execute("""
                    INSERT INTO shipments (order_id, carrier_name, tracking_number, shipment_date, estimated_delivery_date, status)
                    VALUES (?, ?, ?, ?, ?, 'In Transit')
                """, (order_id, carrier, tracking, ship_date, est_date))
                conn.execute("UPDATE customer_orders SET status = 'Shipped' WHERE order_id = ?", (order_id,))
                conn.commit()
                flash("Shipment logged successfully!", "success")
            except sqlite3.Error as e:
                conn.rollback()
                flash(f"Error logging shipment: {e}", "danger")
                
        elif action == "update_status":
            shipment_id = request.form.get("shipment_id")
            status_ship = request.form.get("status")
            sig_name = request.form.get("delivery_signature_name")
            
            try:
                if status_ship == "Delivered":
                    conn.execute("""
                        UPDATE shipments 
                        SET status = ?, actual_delivery_date = STRFTIME('%Y-%m-%d', 'now'), delivery_signature_name = ?
                        WHERE shipment_id = ?
                    """, (status_ship, sig_name, shipment_id))
                    
                    # Fetch order_id
                    order_id = conn.execute("SELECT order_id FROM shipments WHERE shipment_id = ?", (shipment_id,)).fetchone()[0]
                    conn.execute("UPDATE customer_orders SET status = 'Delivered' WHERE order_id = ?", (order_id,))
                else:
                    conn.execute("UPDATE shipments SET status = ? WHERE shipment_id = ?", (status_ship, shipment_id))
                    
                conn.commit()
                flash("Shipment status updated successfully!", "success")
            except sqlite3.Error as e:
                conn.rollback()
                flash(f"Error updating shipment: {e}", "danger")
                
        return redirect(url_for("shipments"))
        
    shipments_list = conn.execute("""
        SELECT s.*, co.total_amount, c.company_name, c.contact_name 
        FROM shipments s 
        JOIN customer_orders co ON s.order_id = co.order_id 
        JOIN customers c ON co.customer_id = c.customer_id
        ORDER BY s.shipment_id DESC
    """).fetchall()
    
    pending_orders_select = conn.execute("""
        SELECT order_id, total_amount 
        FROM customer_orders 
        WHERE status = 'Pending' AND order_id NOT IN (SELECT order_id FROM shipments)
    """).fetchall()
    
    conn.close()
    return render_template("shipments.html", shipments_list=shipments_list, pending_orders_select=pending_orders_select)

@app.route("/analytics")
def analytics():
    if not is_logged_in():
        return redirect(url_for("login"))
    return render_template("analytics.html")

# ----------------------------------------------------------------------------
# JSON API ENDPOINTS FOR CHARTS
# ----------------------------------------------------------------------------

@app.route("/api/analytics/production_efficiency")
def api_production_efficiency():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    # Query 1: Artisan production efficiency
    query = """
        SELECT 
            a.first_name || ' ' || a.last_name AS artisan_name,
            d.design_name,
            ROUND(AVG(d.estimated_production_days), 1) AS est,
            ROUND(AVG(JULIANDAY(b.actual_completion_date) - JULIANDAY(b.start_date)), 1) AS act
        FROM artisans a
        JOIN production_batches b ON a.artisan_id = b.artisan_id
        JOIN designs d ON b.design_id = d.design_id
        WHERE b.status = 'Completed'
        GROUP BY a.artisan_id, d.design_id;
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    
    labels = [f"{r['artisan_name']} ({r['design_name']})" for r in rows]
    estimated = [r['est'] for r in rows]
    actual = [r['act'] for r in rows]
    
    return jsonify({
        "labels": labels,
        "estimated": estimated,
        "actual": actual
    })

@app.route("/api/analytics/delays")
def api_delays():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
        
    conn = get_db_connection()
    # Query 2: Bottlenecks/Delays
    query = """
        SELECT 
            pd.reason_category,
            COUNT(pd.delay_id) AS incidents,
            SUM(CASE 
                WHEN pd.resolved_date IS NOT NULL THEN (JULIANDAY(pd.resolved_date) - JULIANDAY(pd.start_date))
                ELSE (JULIANDAY('now') - JULIANDAY(pd.start_date))
            END) AS days
        FROM production_delays pd
        GROUP BY pd.reason_category;
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    
    categories = [r['reason_category'] for r in rows]
    incidents = [r['incidents'] for r in rows]
    days = [r['days'] for r in rows]
    
    return jsonify({
        "categories": categories,
        "incidents": incidents,
        "days": days
    })

@app.route("/api/analytics/sustainability")
def api_sustainability():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
        
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM vw_sustainability_metrics").fetchone()
    conn.close()
    
    if not row:
        return jsonify({
            "labels": ["Eco-friendly", "Other"],
            "values": [0, 0]
        })
        
    return jsonify({
        "eco_material_percentage": row["eco_material_percentage"],
        "natural_dye_ratio_percent": row["natural_dye_ratio_percent"],
        "eco_friendly_kg": row["eco_friendly_materials_kg"],
        "total_material_kg": row["total_materials_used_kg"],
        "natural_dye_kg": row["natural_dye_used_kg"],
        "synthetic_dye_kg": row["synthetic_dye_used_kg"]
    })

@app.route("/api/analytics/profitability")
def api_profitability():
    if not is_logged_in():
        return jsonify({"error": "Unauthorized"}), 401
        
    conn = get_db_connection()
    # Query 4: Ledger Profitability
    query = """
        SELECT 
            d.design_name,
            ROUND(AVG(wp.net_wage), 2) AS labor_cost,
            ROUND(AVG(COALESCE(bmu.quantity_used * rm.cost_per_unit, 0.0)), 2) AS material_cost,
            ROUND(AVG(b.quantity_meters * COALESCE((SELECT AVG(unit_price) FROM order_items WHERE design_id = d.design_id), d.complexity_multiplier * 1500.0)), 2) AS revenue
        FROM production_batches b
        JOIN designs d ON b.design_id = d.design_id
        LEFT JOIN batch_material_usage bmu ON b.batch_id = bmu.batch_id
        LEFT JOIN raw_materials rm ON bmu.material_id = rm.material_id
        LEFT JOIN wage_payments wp ON b.batch_id = wp.batch_id
        WHERE b.status = 'Completed'
        GROUP BY d.design_id;
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    
    designs = [r['design_name'] for r in rows]
    costs = [round(r['labor_cost'] + r['material_cost'], 2) for r in rows]
    revenue = [r['revenue'] for r in rows]
    profits = [round(r['revenue'] - (r['labor_cost'] + r['material_cost']), 2) for r in rows]
    
    return jsonify({
        "designs": designs,
        "costs": costs,
        "revenue": revenue,
        "profits": profits
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0",
port=int(os.environ.get("PORT",5000))

-- ============================================================================
-- Heritage Textile Intelligence & Supply Chain Management System
-- SQLite Schema DDL
-- Compatible only with SQLite.
-- Enforce Foreign Key Support in SQLite: PRAGMA foreign_keys = ON;
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ============================================================================
-- CLEANUP: Drop existing views, triggers, and tables (Reverse Dependency Order)
-- ============================================================================

DROP VIEW IF EXISTS vw_order_fulfillment_status;
DROP VIEW IF EXISTS vw_inventory_status;
DROP VIEW IF EXISTS vw_active_supply_chain;
DROP VIEW IF EXISTS vw_sustainability_metrics;
DROP VIEW IF EXISTS vw_artisan_performance;

DROP TRIGGER IF EXISTS tg_apply_qc_wage_adjustment;
DROP TRIGGER IF EXISTS tg_generate_authenticity_record;
DROP TRIGGER IF EXISTS tg_calculate_wage_on_completion;
DROP TRIGGER IF EXISTS tg_check_inventory_alert;
DROP TRIGGER IF EXISTS tg_deduct_inventory_on_batch_start;

DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS customer_orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS authenticity_records;
DROP TABLE IF EXISTS inventory_alerts;
DROP TABLE IF EXISTS wage_payments;
DROP TABLE IF EXISTS rework_logs;
DROP TABLE IF EXISTS inspections;
DROP TABLE IF EXISTS production_delays;
DROP TABLE IF EXISTS batch_material_usage;
DROP TABLE IF EXISTS production_batches;
DROP TABLE IF EXISTS supplier_materials;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS raw_materials;
DROP TABLE IF EXISTS designs;
DROP TABLE IF EXISTS looms;
DROP TABLE IF EXISTS artisans;
DROP TABLE IF EXISTS users;

-- ============================================================================
-- 11. USER / ROLE MANAGEMENT
-- ============================================================================

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Admin', 'Inventory Manager', 'QC Inspector', 'Finance Manager')),
    status TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Suspended')),
    created_at TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now'))
);

-- ============================================================================
-- 1. ARTISAN MANAGEMENT
-- ============================================================================

CREATE TABLE artisans (
    artisan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    experience_years INTEGER NOT NULL CHECK (experience_years >= 0),
    skill_level TEXT NOT NULL CHECK (skill_level IN ('Beginner', 'Intermediate', 'Master')),
    specialization TEXT NOT NULL,
    base_wage_rate REAL NOT NULL CHECK (base_wage_rate > 0.0),
    certification_details TEXT,
    status TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'On Leave')),
    created_at TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now'))
);

-- ============================================================================
-- 2. LOOM MANAGEMENT
-- ============================================================================

CREATE TABLE looms (
    loom_id INTEGER PRIMARY KEY AUTOINCREMENT,
    loom_type TEXT NOT NULL,
    installation_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    last_maintenance_date TEXT,      -- Format: YYYY-MM-DD
    maintenance_interval_days INTEGER NOT NULL DEFAULT 90 CHECK (maintenance_interval_days > 0),
    efficiency_rating REAL NOT NULL DEFAULT 100.0 CHECK (efficiency_rating >= 0.0 AND efficiency_rating <= 100.0),
    status TEXT NOT NULL DEFAULT 'Available' CHECK (status IN ('Available', 'In Use', 'Under Maintenance', 'Retired'))
);

-- ============================================================================
-- 3. DESIGN / MOTIF MANAGEMENT
-- ============================================================================

CREATE TABLE designs (
    design_id INTEGER PRIMARY KEY AUTOINCREMENT,
    design_name TEXT UNIQUE NOT NULL,
    regional_origin TEXT NOT NULL,
    complexity_multiplier REAL NOT NULL DEFAULT 1.0 CHECK (complexity_multiplier >= 1.0 AND complexity_multiplier <= 3.0),
    estimated_production_days INTEGER NOT NULL CHECK (estimated_production_days > 0),
    cultural_significance TEXT,
    eco_score INTEGER NOT NULL CHECK (eco_score >= 1 AND eco_score <= 100),
    created_at TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d', 'now'))
);

-- ============================================================================
-- 4. RAW MATERIAL INVENTORY & 15. SUSTAINABILITY METRICS
-- ============================================================================

CREATE TABLE raw_materials (
    material_id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_name TEXT NOT NULL,
    material_type TEXT NOT NULL CHECK (material_type IN ('Yarn', 'Dye', 'Zari', 'Chemical', 'Other')),
    dye_type TEXT NOT NULL DEFAULT 'None' CHECK (dye_type IN ('Natural', 'Synthetic', 'None')),
    unit_of_measure TEXT NOT NULL,
    stock_quantity REAL NOT NULL DEFAULT 0.0 CHECK (stock_quantity >= 0.0),
    reorder_level REAL NOT NULL CHECK (reorder_level >= 0.0),
    cost_per_unit REAL NOT NULL CHECK (cost_per_unit >= 0.0),
    quality_grade TEXT NOT NULL CHECK (quality_grade IN ('Premium', 'Standard', 'Economy')),
    eco_friendly INTEGER NOT NULL DEFAULT 0 CHECK (eco_friendly IN (0, 1)) -- 1 for Eco-friendly, 0 otherwise
);

-- ============================================================================
-- 5. SUPPLIER MANAGEMENT
-- ============================================================================

CREATE TABLE suppliers (
    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT NOT NULL,
    contact_person TEXT,
    phone TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    address TEXT,
    sustainability_rating REAL CHECK (sustainability_rating IS NULL OR (sustainability_rating >= 1.0 AND sustainability_rating <= 5.0))
);

-- Association table for Suppliers and Raw Materials (Normalizing M:N relationship)
CREATE TABLE supplier_materials (
    supplier_id INTEGER,
    material_id INTEGER,
    supply_lead_time_days INTEGER NOT NULL CHECK (supply_lead_time_days > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0.0),
    PRIMARY KEY (supplier_id, material_id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES raw_materials (material_id) ON DELETE CASCADE
);

-- ============================================================================
-- 6. PRODUCTION TRACKING
-- ============================================================================

CREATE TABLE production_batches (
    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    design_id INTEGER NOT NULL,
    artisan_id INTEGER NOT NULL,
    loom_id INTEGER NOT NULL,
    start_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    target_completion_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    actual_completion_date TEXT, -- Format: YYYY-MM-DD
    quantity_meters REAL NOT NULL CHECK (quantity_meters > 0.0),
    status TEXT NOT NULL DEFAULT 'Scheduled' CHECK (status IN ('Scheduled', 'In Progress', 'Completed', 'On Hold', 'Cancelled')),
    FOREIGN KEY (design_id) REFERENCES designs (design_id),
    FOREIGN KEY (artisan_id) REFERENCES artisans (artisan_id),
    FOREIGN KEY (loom_id) REFERENCES looms (loom_id)
);

-- Association table for Material Usage in Production Batches (Normalizing M:N relationship)
CREATE TABLE batch_material_usage (
    batch_id INTEGER,
    material_id INTEGER,
    quantity_used REAL NOT NULL CHECK (quantity_used > 0.0),
    PRIMARY KEY (batch_id, material_id),
    FOREIGN KEY (batch_id) REFERENCES production_batches (batch_id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES raw_materials (material_id)
);

-- Track delays in production lifecycle
CREATE TABLE production_delays (
    delay_id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    reason_category TEXT NOT NULL CHECK (reason_category IN ('Material Shortage', 'Artisan Illness', 'Loom Breakdown', 'Power Outage', 'Design Change', 'Other')),
    description TEXT NOT NULL,
    start_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    resolved_date TEXT,       -- Format: YYYY-MM-DD
    FOREIGN KEY (batch_id) REFERENCES production_batches (batch_id) ON DELETE CASCADE
);

-- ============================================================================
-- 7. QUALITY CONTROL
-- ============================================================================

CREATE TABLE inspections (
    inspection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    inspector_id INTEGER NOT NULL,
    inspection_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    quality_score REAL NOT NULL CHECK (quality_score >= 0.0 AND quality_score <= 100.0),
    status TEXT NOT NULL CHECK (status IN ('Passed', 'Failed', 'Rework Required')),
    defects_found TEXT,
    FOREIGN KEY (batch_id) REFERENCES production_batches (batch_id),
    FOREIGN KEY (inspector_id) REFERENCES users (user_id)
);

-- ============================================================================
-- 14. REWORK / DEFECT MANAGEMENT
-- ============================================================================

CREATE TABLE rework_logs (
    rework_id INTEGER PRIMARY KEY AUTOINCREMENT,
    inspection_id INTEGER NOT NULL,
    defect_type TEXT NOT NULL,
    rework_instructions TEXT,
    assigned_artisan_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Assigned' CHECK (status IN ('Assigned', 'In Progress', 'Completed', 'Failed')),
    completion_date TEXT, -- Format: YYYY-MM-DD
    FOREIGN KEY (inspection_id) REFERENCES inspections (inspection_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_artisan_id) REFERENCES artisans (artisan_id)
);

-- ============================================================================
-- 8. WAGE PAYMENT MANAGEMENT
-- ============================================================================

CREATE TABLE wage_payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    artisan_id INTEGER NOT NULL,
    batch_id INTEGER NOT NULL,
    payment_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    calculated_wage REAL NOT NULL CHECK (calculated_wage >= 0.0),
    bonus_applied REAL DEFAULT 0.0 CHECK (bonus_applied >= 0.0),
    deductions REAL DEFAULT 0.0 CHECK (deductions >= 0.0),
    net_wage REAL NOT NULL CHECK (net_wage >= 0.0),
    payment_status TEXT NOT NULL DEFAULT 'Pending' CHECK (payment_status IN ('Pending', 'Processed', 'Paid')),
    FOREIGN KEY (artisan_id) REFERENCES artisans (artisan_id),
    FOREIGN KEY (batch_id) REFERENCES production_batches (batch_id)
);

-- ============================================================================
-- 9. INVENTORY ALERT SYSTEM
-- ============================================================================

CREATE TABLE inventory_alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER NOT NULL,
    alert_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    current_stock REAL NOT NULL,
    reorder_level REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Resolved')),
    FOREIGN KEY (material_id) REFERENCES raw_materials (material_id) ON DELETE CASCADE
);

-- ============================================================================
-- 10. AUTHENTICITY VERIFICATION
-- ============================================================================

CREATE TABLE authenticity_records (
    verification_code TEXT PRIMARY KEY, -- Unique generated code: TX-YYYY-XXXX
    batch_id INTEGER UNIQUE NOT NULL,
    qr_code_url TEXT NOT NULL,
    generation_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    blockchain_hash TEXT NOT NULL,  -- Simulated SHA-256 string
    verification_count INTEGER NOT NULL DEFAULT 0 CHECK (verification_count >= 0),
    FOREIGN KEY (batch_id) REFERENCES production_batches (batch_id)
);

-- ============================================================================
-- 12. CUSTOMER / ORDER MANAGEMENT
-- ============================================================================

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT,
    contact_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    billing_address TEXT,
    shipping_address TEXT,
    created_at TEXT NOT NULL DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S', 'now'))
);

CREATE TABLE customer_orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    required_delivery_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    status TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled')),
    total_amount REAL NOT NULL DEFAULT 0.0 CHECK (total_amount >= 0.0),
    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

-- Order Items (Normalizing Order details)
CREATE TABLE order_items (
    order_id INTEGER,
    design_id INTEGER,
    quantity_meters REAL NOT NULL CHECK (quantity_meters > 0.0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0.0),
    PRIMARY KEY (order_id, design_id),
    FOREIGN KEY (order_id) REFERENCES customer_orders (order_id) ON DELETE CASCADE,
    FOREIGN KEY (design_id) REFERENCES designs (design_id)
);

-- ============================================================================
-- 13. SHIPMENT / DELIVERY TRACKING
-- ============================================================================

CREATE TABLE shipments (
    shipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER UNIQUE NOT NULL,
    carrier_name TEXT NOT NULL,
    tracking_number TEXT UNIQUE NOT NULL,
    shipment_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    estimated_delivery_date TEXT, -- Format: YYYY-MM-DD
    actual_delivery_date TEXT,    -- Format: YYYY-MM-DD
    status TEXT NOT NULL DEFAULT 'In Transit' CHECK (status IN ('In Transit', 'Out for Delivery', 'Delivered', 'Returned', 'Delayed')),
    delivery_signature_name TEXT,
    FOREIGN KEY (order_id) REFERENCES customer_orders (order_id)
);


-- ============================================================================
-- ADVANCED DBMS FEATURES: TRIGGERS
-- ============================================================================

-- Trigger 1: Automatically deduct raw material inventory when a production batch starts ('In Progress')
CREATE TRIGGER tg_deduct_inventory_on_batch_start
AFTER UPDATE OF status ON production_batches
WHEN NEW.status = 'In Progress' AND OLD.status != 'In Progress'
BEGIN
    UPDATE raw_materials
    SET stock_quantity = stock_quantity - (
        SELECT quantity_used 
        FROM batch_material_usage 
        WHERE batch_material_usage.material_id = raw_materials.material_id 
          AND batch_material_usage.batch_id = NEW.batch_id
    )
    WHERE material_id IN (
        SELECT material_id 
        FROM batch_material_usage 
        WHERE batch_id = NEW.batch_id
    );
END;

-- Trigger 2: Check for low-stock and insert alert if stock falls below reorder level
CREATE TRIGGER tg_check_inventory_alert
AFTER UPDATE OF stock_quantity ON raw_materials
WHEN NEW.stock_quantity <= NEW.reorder_level
BEGIN
    INSERT INTO inventory_alerts (material_id, alert_date, current_stock, reorder_level, status)
    SELECT NEW.material_id, STRFTIME('%Y-%m-%d', 'now'), NEW.stock_quantity, NEW.reorder_level, 'Active'
    WHERE NOT EXISTS (
        SELECT 1 FROM inventory_alerts 
        WHERE material_id = NEW.material_id AND status = 'Active'
    );
END;

-- Trigger 3: Automatically calculate and create wage payment when a production batch is marked 'Completed'
CREATE TRIGGER tg_calculate_wage_on_completion
AFTER UPDATE OF status ON production_batches
WHEN NEW.status = 'Completed' AND OLD.status != 'Completed'
BEGIN
    INSERT INTO wage_payments (artisan_id, batch_id, payment_date, calculated_wage, bonus_applied, deductions, net_wage, payment_status)
    SELECT 
        NEW.artisan_id,
        NEW.batch_id,
        STRFTIME('%Y-%m-%d', 'now'),
        (NEW.quantity_meters * a.base_wage_rate * d.complexity_multiplier) as calc_wage,
        0.0,
        0.0,
        (NEW.quantity_meters * a.base_wage_rate * d.complexity_multiplier) as net_wg,
        'Pending'
    FROM artisans a
    JOIN designs d ON d.design_id = NEW.design_id
    WHERE a.artisan_id = NEW.artisan_id;
END;

-- Trigger 4: Automatically generate authenticity record when production batch is marked 'Completed'
CREATE TRIGGER tg_generate_authenticity_record
AFTER UPDATE OF status ON production_batches
WHEN NEW.status = 'Completed' AND OLD.status != 'Completed'
BEGIN
    INSERT INTO authenticity_records (verification_code, batch_id, qr_code_url, generation_date, blockchain_hash, verification_count)
    VALUES (
        'TX-' || STRFTIME('%Y', 'now') || '-' || PRINTF('%04d', NEW.batch_id),
        NEW.batch_id,
        'https://verify.heritagetextile.org/verify/' || NEW.batch_id,
        STRFTIME('%Y-%m-%d', 'now'),
        LOWER(HEX(RANDOMBLOB(32))), -- Simulated cryptographically secure unique SHA-256 blockchain hash
        0
    );
END;

-- Trigger 5: Apply QC wage adjustment (Bonus for high score, deduction & Rework logging for failed inspections)
CREATE TRIGGER tg_apply_qc_wage_adjustment
AFTER INSERT ON inspections
BEGIN
    -- Apply 10% quality bonus if score is >= 95.0 and status is 'Passed'
    UPDATE wage_payments
    SET bonus_applied = calculated_wage * 0.10,
        net_wage = (calculated_wage * 1.10) - deductions
    WHERE batch_id = NEW.batch_id AND NEW.status = 'Passed' AND NEW.quality_score >= 95.0;

    -- Apply 15% quality penalty/deduction if status is 'Failed' or 'Rework Required'
    UPDATE wage_payments
    SET deductions = calculated_wage * 0.15,
        net_wage = CASE 
            WHEN (calculated_wage * 0.85) + bonus_applied < 0.0 THEN 0.0
            ELSE (calculated_wage * 0.85) + bonus_applied
        END
    WHERE batch_id = NEW.batch_id AND NEW.status IN ('Failed', 'Rework Required');

    -- Automatically log a rework entry if the status is 'Rework Required'
    INSERT INTO rework_logs (inspection_id, defect_type, rework_instructions, assigned_artisan_id, status)
    SELECT 
        NEW.inspection_id,
        COALESCE(NEW.defects_found, 'Unspecified Defect'),
        'QC Inspection failed with score ' || NEW.quality_score || '. Defects found: ' || COALESCE(NEW.defects_found, 'None detailed') || '. Please perform corrective weaving.',
        b.artisan_id,
        'Assigned'
    FROM production_batches b
    WHERE b.batch_id = NEW.batch_id AND NEW.status = 'Rework Required';
END;


-- ============================================================================
-- ADVANCED DBMS FEATURES: VIEWS
-- ============================================================================

-- View 1: Artisan Performance Dashboard
CREATE VIEW vw_artisan_performance AS
SELECT 
    a.artisan_id,
    a.first_name || ' ' || a.last_name AS artisan_name,
    a.experience_years,
    a.skill_level,
    a.specialization,
    COUNT(b.batch_id) AS total_batches,
    SUM(CASE WHEN b.status = 'Completed' THEN b.quantity_meters ELSE 0.0 END) AS total_meters_produced,
    ROUND(AVG(i.quality_score), 2) AS avg_quality_score,
    ROUND(SUM(wp.net_wage), 2) AS total_wages_earned,
    SUM(CASE WHEN JULIANDAY(b.actual_completion_date) > JULIANDAY(b.target_completion_date) THEN 1 ELSE 0 END) AS delayed_batches_count
FROM artisans a
LEFT JOIN production_batches b ON a.artisan_id = b.artisan_id
LEFT JOIN inspections i ON b.batch_id = i.batch_id
LEFT JOIN wage_payments wp ON b.batch_id = wp.batch_id
GROUP BY a.artisan_id;

-- View 2: Environmental Sustainability & Eco-Metrics Dashboard
CREATE VIEW vw_sustainability_metrics AS
SELECT 
    COUNT(b.batch_id) AS total_batches_tracked,
    ROUND(AVG(d.eco_score), 2) AS avg_design_eco_score,
    SUM(CASE WHEN rm.eco_friendly = 1 THEN bmu.quantity_used ELSE 0.0 END) AS eco_friendly_materials_kg,
    SUM(bmu.quantity_used) AS total_materials_used_kg,
    ROUND((SUM(CASE WHEN rm.eco_friendly = 1 THEN bmu.quantity_used ELSE 0.0 END) / SUM(bmu.quantity_used)) * 100.0, 2) AS eco_material_percentage,
    SUM(CASE WHEN rm.dye_type = 'Natural' THEN bmu.quantity_used ELSE 0.0 END) AS natural_dye_used_kg,
    SUM(CASE WHEN rm.dye_type = 'Synthetic' THEN bmu.quantity_used ELSE 0.0 END) AS synthetic_dye_used_kg,
    ROUND((SUM(CASE WHEN rm.dye_type = 'Natural' THEN bmu.quantity_used ELSE 0.0 END) / 
           SUM(CASE WHEN rm.dye_type IN ('Natural', 'Synthetic') THEN bmu.quantity_used ELSE 0.0 END)) * 100.0, 2) AS natural_dye_ratio_percent
FROM production_batches b
JOIN designs d ON b.design_id = d.design_id
JOIN batch_material_usage bmu ON b.batch_id = bmu.batch_id
JOIN raw_materials rm ON bmu.material_id = rm.material_id
WHERE b.status = 'Completed';

-- View 3: Active Supply Chain & Production Status
CREATE VIEW vw_active_supply_chain AS
SELECT 
    b.batch_id,
    d.design_name,
    a.first_name || ' ' || a.last_name AS artisan_name,
    l.loom_id,
    l.loom_type,
    b.start_date,
    b.target_completion_date,
    b.quantity_meters,
    b.status AS production_status,
    CASE 
        WHEN b.status = 'In Progress' AND STRFTIME('%Y-%m-%d', 'now') > b.target_completion_date THEN 'Delayed'
        WHEN b.status = 'In Progress' THEN 'On Schedule'
        ELSE b.status
    END AS timeline_status,
    COALESCE(SUM(pd.delay_id), 0) AS recorded_delays_count
FROM production_batches b
JOIN designs d ON b.design_id = d.design_id
JOIN artisans a ON b.artisan_id = a.artisan_id
JOIN looms l ON b.loom_id = l.loom_id
LEFT JOIN production_delays pd ON b.batch_id = pd.batch_id AND pd.resolved_date IS NULL
WHERE b.status NOT IN ('Completed', 'Cancelled')
GROUP BY b.batch_id;

-- View 4: Real-time Inventory Status & Alerts
CREATE VIEW vw_inventory_status AS
SELECT 
    rm.material_id,
    rm.material_name,
    rm.material_type,
    rm.quality_grade,
    rm.stock_quantity,
    rm.reorder_level,
    rm.unit_of_measure,
    CASE 
        WHEN rm.stock_quantity = 0.0 THEN 'Out of Stock'
        WHEN rm.stock_quantity <= rm.reorder_level THEN 'Low Stock'
        ELSE 'Sufficient'
    END AS stock_status,
    COALESCE(al.alert_date, 'No Active Alert') AS last_alert_date,
    s.supplier_name,
    s.phone AS supplier_phone,
    s.email AS supplier_email
FROM raw_materials rm
LEFT JOIN inventory_alerts al ON rm.material_id = al.material_id AND al.status = 'Active'
LEFT JOIN supplier_materials sm ON rm.material_id = sm.material_id
LEFT JOIN suppliers s ON sm.supplier_id = s.supplier_id;

-- View 5: Customer Order Fulfillment Summary
CREATE VIEW vw_order_fulfillment_status AS
SELECT 
    co.order_id,
    c.contact_name AS customer_name,
    c.company_name,
    co.order_date,
    co.required_delivery_date,
    co.status AS order_status,
    co.total_amount,
    COUNT(oi.design_id) AS distinct_designs_ordered,
    SUM(oi.quantity_meters) AS total_meters_ordered,
    COALESCE(s.tracking_number, 'Not Shipped') AS tracking_number,
    COALESCE(s.status, 'N/A') AS shipment_status
FROM customer_orders co
JOIN customers c ON co.customer_id = c.customer_id
LEFT JOIN order_items oi ON co.order_id = oi.order_id
LEFT JOIN shipments s ON co.order_id = s.order_id
GROUP BY co.order_id;

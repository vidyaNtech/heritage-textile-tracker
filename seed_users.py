import sqlite3, os

DB_PATH = os.path.join('database', 'heritage_tracker.db')
conn = sqlite3.connect(DB_PATH)
conn.execute('PRAGMA foreign_keys = ON')
cur = conn.cursor()

# Clear existing users
cur.execute('DELETE FROM users')

# Insert all 4 role users
users = [
    ('admin_user', 'admin_user$admin', 'Aravind Swamy', 'admin@heritage.com', 'Admin'),
    ('inv_mgr', 'inv_mgr$inv', 'Lakshmi Devi', 'lakshmi@heritage.com', 'Inventory Manager'),
    ('qc_inspect', 'qc_inspect$qc', 'Suresh Nair', 'suresh@heritage.com', 'QC Inspector'),
    ('fin_mgr', 'fin_mgr$fin', 'Priya Menon', 'priya@heritage.com', 'Finance Manager'),
]

for u in users:
    cur.execute('INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)', u)

conn.commit()
conn.close()
print('All 4 role users inserted successfully!')

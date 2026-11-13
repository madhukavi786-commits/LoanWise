"""
LoanWise - Database Layer (SQLite)
Manages connection, schema creation, prediction record persistence,
user authentication, role-based queries, dynamic statistics, and CSV export.
"""

import os
import sqlite3
import csv
import io
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(BASE_DIR, "database", "loanwise.db")
)


def get_db_connection():
    """Returns a SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema, indexes, migrations, and default users."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Predictions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT UNIQUE NOT NULL,
            applicant_name TEXT DEFAULT 'Applicant',
            gender TEXT NOT NULL,
            married TEXT NOT NULL,
            dependents TEXT NOT NULL,
            education TEXT NOT NULL,
            self_employed TEXT NOT NULL,
            applicant_income REAL NOT NULL,
            coapplicant_income REAL NOT NULL,
            loan_amount REAL NOT NULL,
            loan_amount_term REAL NOT NULL,
            credit_history REAL NOT NULL,
            property_area TEXT NOT NULL,
            prediction INTEGER NOT NULL,
            probability REAL NOT NULL,
            risk_level TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Users Table for Authentication & Role-Based Access Control
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Safe Schema Migration (Add missing columns to predictions if not exist)
    cursor.execute("PRAGMA table_info(predictions)")
    columns = [row['name'] for row in cursor.fetchall()]

    if 'user_id' not in columns:
        cursor.execute("ALTER TABLE predictions ADD COLUMN user_id INTEGER REFERENCES users(id)")

    if 'emi_amount' not in columns:
        cursor.execute("ALTER TABLE predictions ADD COLUMN emi_amount REAL DEFAULT 0.0")

    if 'interest_rate' not in columns:
        cursor.execute("ALTER TABLE predictions ADD COLUMN interest_rate REAL DEFAULT 9.5")

    # 4. Indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_app_id ON predictions(application_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')

    # 5. Pre-seed Default Admin and Demo Customer accounts if none exist
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    if user_count == 0:
        admin_hash = generate_password_hash("Admin@123")
        customer_hash = generate_password_hash("Customer@123")

        cursor.execute('''
            INSERT INTO users (username, email, full_name, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', 'admin@loanwise.com', 'System Administrator', admin_hash, 'admin'))

        cursor.execute('''
            INSERT INTO users (username, email, full_name, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ('customer', 'customer@loanwise.com', 'Demo Customer', customer_hash, 'customer'))

    conn.commit()
    conn.close()


# =====================================================================
# USER AUTHENTICATION & MANAGEMENT
# =====================================================================

def create_user(username, email, full_name, password, role='customer'):
    """Registers a new user with hashed password."""
    conn = get_db_connection()
    cursor = conn.cursor()

    username = username.strip().lower()
    email = email.strip().lower()
    full_name = full_name.strip()

    # Check existence
    cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
    if cursor.fetchone():
        conn.close()
        raise ValueError("Username or Email address already registered.")

    hashed_pw = generate_password_hash(password)
    valid_role = 'admin' if role == 'admin' else 'customer'

    cursor.execute('''
        INSERT INTO users (username, email, full_name, password_hash, role)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, email, full_name, hashed_pw, valid_role))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def authenticate_user(username_or_email, password):
    """Authenticates credentials against username or email. Returns user dict or None."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query_val = username_or_email.strip().lower()
    cursor.execute('''
        SELECT * FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?
    ''', (query_val, query_val))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        return dict(user)
    return None


def get_user_by_id(user_id):
    """Fetches user record by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, full_name, role, created_at FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_username(username):
    """Fetches user record by username."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, full_name, role, created_at FROM users WHERE LOWER(username) = ?', (username.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users():
    """Lists all users for administrative monitoring."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, full_name, role, created_at FROM users ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_user_profile(user_id, full_name, email, new_password=None):
    """Updates user profile information and optional password."""
    conn = get_db_connection()
    cursor = conn.cursor()

    email_clean = email.strip().lower()
    full_name_clean = full_name.strip()

    # Check if email is taken by someone else
    cursor.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email_clean, user_id))
    if cursor.fetchone():
        conn.close()
        raise ValueError("Email address already in use by another account.")

    if new_password and len(new_password.strip()) >= 6:
        new_hash = generate_password_hash(new_password.strip())
        cursor.execute('''
            UPDATE users SET full_name = ?, email = ?, password_hash = ? WHERE id = ?
        ''', (full_name_clean, email_clean, new_hash, user_id))
    else:
        cursor.execute('''
            UPDATE users SET full_name = ?, email = ? WHERE id = ?
        ''', (full_name_clean, email_clean, user_id))

    conn.commit()
    conn.close()
    return True


# =====================================================================
# PREDICTION OPERATIONS
# =====================================================================

def generate_application_id():
    """Generates a unique, professional Application ID like LW-2026-1001."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM predictions')
    count = cursor.fetchone()[0]
    conn.close()

    year = datetime.now().year
    return f"LW-{year}-{1001 + count}"


def insert_prediction(data, user_id=None):
    """
    Inserts a new prediction record into the SQLite database.
    Associates the record with the user_id if provided.
    Returns the newly assigned application_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    app_id = data.get('application_id') or generate_application_id()
    applicant_name = data.get('applicant_name', 'Applicant').strip() or 'Applicant'
    assigned_user_id = user_id or data.get('user_id')
    emi_val = float(data.get('emi_amount', 0.0))
    rate_val = float(data.get('interest_rate', 9.5))

    cursor.execute('''
        INSERT INTO predictions (
            application_id, applicant_name, gender, married, dependents,
            education, self_employed, applicant_income, coapplicant_income,
            loan_amount, loan_amount_term, credit_history, property_area,
            prediction, probability, risk_level, user_id, emi_amount,
            interest_rate, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        app_id,
        applicant_name,
        data['gender'],
        data['married'],
        str(data['dependents']),
        data['education'],
        data['self_employed'],
        float(data['applicant_income']),
        float(data['coapplicant_income']),
        float(data['loan_amount']),
        float(data['loan_amount_term']),
        float(data['credit_history']),
        data['property_area'],
        int(data['prediction']),
        round(float(data['probability']), 4),
        data['risk_level'],
        assigned_user_id,
        round(emi_val, 2),
        round(rate_val, 2),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))

    conn.commit()
    conn.close()
    return app_id


def get_prediction_by_id(app_id):
    """Fetches a single prediction record by Application ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM predictions WHERE application_id = ?', (app_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_predictions(search=None, status_filter=None, sort_order='desc', user_id=None, limit=None, offset=None):
    """
    Retrieves prediction records with optional search, status filtering,
    role-based user isolation, sorting, and pagination.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM predictions WHERE 1=1'
    params = []

    # Role-based filtering: customer sees only their records
    if user_id is not None:
        query += ' AND user_id = ?'
        params.append(user_id)

    if search:
        search_term = f"%{search.strip()}%"
        query += ''' AND (
            application_id LIKE ? OR
            applicant_name LIKE ? OR
            property_area LIKE ? OR
            education LIKE ?
        )'''
        params.extend([search_term, search_term, search_term, search_term])

    if status_filter is not None and status_filter != 'all':
        if status_filter in [1, '1', 'Approved', 'approved']:
            query += ' AND prediction = 1'
        elif status_filter in [0, '0', 'Rejected', 'rejected']:
            query += ' AND prediction = 0'

    # Sorting
    if sort_order and sort_order.lower() == 'asc':
        query += ' ORDER BY id ASC'
    else:
        query += ' ORDER BY id DESC'

    if limit is not None:
        query += ' LIMIT ?'
        params.append(limit)
        if offset is not None:
            query += ' OFFSET ?'
            params.append(offset)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_predictions(search=None, status_filter=None, user_id=None):
    """Counts matching prediction records for pagination."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = 'SELECT COUNT(*) FROM predictions WHERE 1=1'
    params = []

    if user_id is not None:
        query += ' AND user_id = ?'
        params.append(user_id)

    if search:
        search_term = f"%{search.strip()}%"
        query += ''' AND (
            application_id LIKE ? OR
            applicant_name LIKE ? OR
            property_area LIKE ? OR
            education LIKE ?
        )'''
        params.extend([search_term, search_term, search_term, search_term])

    if status_filter is not None and status_filter != 'all':
        if status_filter in [1, '1', 'Approved', 'approved']:
            query += ' AND prediction = 1'
        elif status_filter in [0, '0', 'Rejected', 'rejected']:
            query += ' AND prediction = 0'

    cursor.execute(query, params)
    total = cursor.fetchone()[0]
    conn.close()
    return total


def get_dashboard_stats(user_id=None, is_admin=True):
    """
    Dynamically computes dashboard metrics from stored prediction records.
    If is_admin is False and user_id is provided, returns stats for that user only.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    filter_clause = " WHERE user_id = ?" if (not is_admin and user_id is not None) else ""
    params = [user_id] if (not is_admin and user_id is not None) else []

    # Total counts
    cursor.execute(f'SELECT COUNT(*) FROM predictions{filter_clause}', params)
    total_applications = cursor.fetchone()[0]

    app_filter = (" AND prediction = 1" if filter_clause else " WHERE prediction = 1")
    cursor.execute(f'SELECT COUNT(*) FROM predictions{filter_clause}{app_filter}', params)
    total_approved = cursor.fetchone()[0]

    rej_filter = (" AND prediction = 0" if filter_clause else " WHERE prediction = 0")
    cursor.execute(f'SELECT COUNT(*) FROM predictions{filter_clause}{rej_filter}', params)
    total_rejected = cursor.fetchone()[0]

    approval_rate = round((total_approved / total_applications * 100), 1) if total_applications > 0 else 0.0

    # Recent 5 predictions
    cursor.execute(f'SELECT * FROM predictions{filter_clause} ORDER BY id DESC LIMIT 5', params)
    recent_rows = cursor.fetchall()
    recent_predictions = [dict(r) for r in recent_rows]

    # Activity chart data: applications grouped by date
    group_clause = f"{filter_clause} GROUP BY DATE(created_at)" if filter_clause else " GROUP BY DATE(created_at)"
    cursor.execute(f'''
        SELECT DATE(created_at) as pred_date,
               SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as approved,
               SUM(CASE WHEN prediction = 0 THEN 1 ELSE 0 END) as rejected,
               COUNT(*) as total
        FROM predictions
        {group_clause}
        ORDER BY pred_date ASC
        LIMIT 7
    ''', params)
    activity_rows = cursor.fetchall()
    activity_data = {
        'dates': [r['pred_date'] for r in activity_rows],
        'approved': [r['approved'] for r in activity_rows],
        'rejected': [r['rejected'] for r in activity_rows]
    }

    # Property Area breakdown
    prop_group = f"{filter_clause} GROUP BY property_area" if filter_clause else " GROUP BY property_area"
    cursor.execute(f'''
        SELECT property_area,
               SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as approved,
               SUM(CASE WHEN prediction = 0 THEN 1 ELSE 0 END) as rejected
        FROM predictions
        {prop_group}
    ''', params)
    property_rows = cursor.fetchall()
    property_stats = [dict(r) for r in property_rows]

    conn.close()

    return {
        'total_applications': total_applications,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'approval_rate': approval_rate,
        'recent_predictions': recent_predictions,
        'doughnut_chart': {
            'labels': ['Approved', 'Rejected'],
            'data': [total_approved, total_rejected]
        },
        'activity_data': activity_data,
        'property_stats': property_stats
    }


def get_risk_analytics_stats(user_id=None, is_admin=True):
    """
    Computes comprehensive, real-data analytical aggregations for the Risk Analytics Dashboard.
    Includes risk tiers, income brackets, credit distributions, loan amount analysis, and averages.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    filter_clause = " WHERE user_id = ?" if (not is_admin and user_id is not None) else ""
    params = [user_id] if (not is_admin and user_id is not None) else []

    # 1. Total overview
    cursor.execute(f'''
        SELECT COUNT(*) as total,
               SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as approved,
               SUM(CASE WHEN prediction = 0 THEN 1 ELSE 0 END) as rejected,
               AVG(loan_amount) as avg_loan,
               AVG(applicant_income) as avg_income
        FROM predictions{filter_clause}
    ''', params)
    row = cursor.fetchone()
    total_apps = row['total'] or 0
    total_appr = row['approved'] or 0
    total_reje = row['rejected'] or 0
    avg_loan = round(float(row['avg_loan'] or 0), 1)
    avg_income = round(float(row['avg_income'] or 0), 1)
    appr_rate = round((total_appr / total_apps * 100), 1) if total_apps > 0 else 0.0

    # 2. Risk Tier Classification
    risk_where = f"{filter_clause} GROUP BY risk_level" if filter_clause else " GROUP BY risk_level"
    cursor.execute(f'''
        SELECT risk_level, COUNT(*) as count
        FROM predictions
        {risk_where}
    ''', params)
    risk_rows = cursor.fetchall()
    risk_distribution = {
        'Low Risk': 0,
        'Moderate Risk': 0,
        'High Risk': 0
    }
    for r in risk_rows:
        rl = r['risk_level']
        if 'Low' in rl:
            risk_distribution['Low Risk'] += r['count']
        elif 'Moderate' in rl:
            risk_distribution['Moderate Risk'] += r['count']
        elif 'High' in rl:
            risk_distribution['High Risk'] += r['count']

    # 3. Income Distribution Brackets
    # Brackets: <$2,500, $2,500-$5,000, $5,000-$10,000, >$10,000
    income_brackets = {
        'Under $2.5k': {'total': 0, 'approved': 0},
        '$2.5k - $5k': {'total': 0, 'approved': 0},
        '$5k - $10k': {'total': 0, 'approved': 0},
        'Above $10k': {'total': 0, 'approved': 0}
    }
    cursor.execute(f'SELECT applicant_income, prediction FROM predictions{filter_clause}', params)
    for p in cursor.fetchall():
        inc = float(p['applicant_income'])
        pred = int(p['prediction'])
        if inc < 2500:
            b = 'Under $2.5k'
        elif inc <= 5000:
            b = '$2.5k - $5k'
        elif inc <= 10000:
            b = '$5k - $10k'
        else:
            b = 'Above $10k'
        income_brackets[b]['total'] += 1
        if pred == 1:
            income_brackets[b]['approved'] += 1

    # 4. Credit History Breakdown
    credit_where = f"{filter_clause} GROUP BY credit_history" if filter_clause else " GROUP BY credit_history"
    cursor.execute(f'''
        SELECT credit_history,
               COUNT(*) as count,
               SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as approved,
               SUM(CASE WHEN prediction = 0 THEN 1 ELSE 0 END) as rejected
        FROM predictions
        {credit_where}
    ''', params)
    credit_stats = {
        'Good Credit (1.0)': {'total': 0, 'approved': 0, 'rejected': 0},
        'Poor Credit (0.0)': {'total': 0, 'approved': 0, 'rejected': 0}
    }
    for r in cursor.fetchall():
        ch_val = float(r['credit_history'])
        key = 'Good Credit (1.0)' if ch_val == 1.0 else 'Poor Credit (0.0)'
        credit_stats[key]['total'] = r['count']
        credit_stats[key]['approved'] = r['approved']
        credit_stats[key]['rejected'] = r['rejected']

    # 5. Loan Amount Brackets (<$100k, $100k-$200k, $200k-$300k, >$300k)
    loan_brackets = {
        '<$100k': {'total': 0, 'approved': 0},
        '$100k-$200k': {'total': 0, 'approved': 0},
        '$200k-$300k': {'total': 0, 'approved': 0},
        '>$300k': {'total': 0, 'approved': 0}
    }
    cursor.execute(f'SELECT loan_amount, prediction FROM predictions{filter_clause}', params)
    for row in cursor.fetchall():
        la = float(row['loan_amount'])
        pred = int(row['prediction'])
        if la < 100:
            b = '<$100k'
        elif la <= 200:
            b = '$100k-$200k'
        elif la <= 300:
            b = '$200k-$300k'
        else:
            b = '>$300k'
        loan_brackets[b]['total'] += 1
        if pred == 1:
            loan_brackets[b]['approved'] += 1

    # 6. Property Area Breakdown
    prop_where = f"{filter_clause} GROUP BY property_area" if filter_clause else " GROUP BY property_area"
    cursor.execute(f'''
        SELECT property_area,
               COUNT(*) as total,
               SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as approved,
               SUM(CASE WHEN prediction = 0 THEN 1 ELSE 0 END) as rejected
        FROM predictions
        {prop_where}
    ''', params)
    prop_stats = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        'total_applications': total_apps,
        'total_approved': total_appr,
        'total_rejected': total_reje,
        'approval_rate': appr_rate,
        'average_loan': avg_loan,
        'average_income': avg_income,
        'risk_distribution': risk_distribution,
        'income_brackets': income_brackets,
        'credit_stats': credit_stats,
        'loan_brackets': loan_brackets,
        'property_stats': prop_stats
    }


def delete_prediction(app_id, user_id=None, is_admin=False):
    """Deletes a single prediction record by Application ID with permission checks."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if is_admin:
        cursor.execute('DELETE FROM predictions WHERE application_id = ?', (app_id,))
    else:
        cursor.execute('DELETE FROM predictions WHERE application_id = ? AND user_id = ?', (app_id, user_id))

    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def clear_history(user_id=None, is_admin=True):
    """Clears records from the predictions table with permission checks."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if is_admin or user_id is None:
        cursor.execute('DELETE FROM predictions')
    else:
        cursor.execute('DELETE FROM predictions WHERE user_id = ?', (user_id,))

    conn.commit()
    conn.close()


def export_predictions_csv(user_id=None, is_admin=False):
    """Generates a CSV string of stored predictions with permission filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if is_admin or user_id is None:
        cursor.execute('SELECT * FROM predictions ORDER BY id DESC')
    else:
        cursor.execute('SELECT * FROM predictions WHERE user_id = ? ORDER BY id DESC', (user_id,))

    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'Application ID', 'Applicant Name', 'Date Submitted',
        'Gender', 'Married', 'Dependents', 'Education', 'Self Employed',
        'Applicant Income ($)', 'Coapplicant Income ($)', 'Loan Amount ($K)',
        'Term (Months)', 'Credit History', 'Property Area',
        'Predicted Status', 'Approval Probability (%)', 'Risk Level', 'EMI ($)'
    ])

    for r in rows:
        status_text = 'Approved' if r['prediction'] == 1 else 'Rejected'
        emi_val = r['emi_amount'] if 'emi_amount' in r.keys() and r['emi_amount'] else 0.0
        writer.writerow([
            r['application_id'],
            r['applicant_name'],
            r['created_at'],
            r['gender'],
            r['married'],
            r['dependents'],
            r['education'],
            r['self_employed'],
            r['applicant_income'],
            r['coapplicant_income'],
            r['loan_amount'],
            r['loan_amount_term'],
            'Meets Guidelines' if r['credit_history'] == 1.0 else 'Does Not Meet',
            r['property_area'],
            status_text,
            round(r['probability'] * 100, 2),
            r['risk_level'],
            emi_val
        ])

    return output.getvalue()

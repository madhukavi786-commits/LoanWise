"""
LoanWise - Database Layer (SQLite)
Manages connection, schema creation, prediction record persistence,
dynamic statistics calculation, filtering, and CSV export.
"""
import os
import sqlite3
import csv
import io
from datetime import datetime
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
    """Initializes the database schema and indexes."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

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

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_predictions_app_id
        ON predictions(application_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_predictions_created_at
        ON predictions(created_at)
    ''')

    conn.commit()
    conn.close()


def generate_application_id():
    """Generates a unique, professional Application ID like LW-2026-1001."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM predictions')
    count = cursor.fetchone()[0]
    conn.close()

    year = datetime.now().year
    return f"LW-{year}-{1001 + count}"


def insert_prediction(data):
    """
    Inserts a new prediction record into the SQLite database.
    Returns the newly assigned application_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    app_id = data.get('application_id') or generate_application_id()
    applicant_name = data.get('applicant_name', 'Applicant').strip() or 'Applicant'

    cursor.execute('''
        INSERT INTO predictions (
            application_id, applicant_name, gender, married, dependents,
            education, self_employed, applicant_income, coapplicant_income,
            loan_amount, loan_amount_term, credit_history, property_area,
            prediction, probability, risk_level, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


def get_all_predictions(search=None, status_filter=None, limit=None, offset=None):
    """
    Retrieves prediction records with optional search, status filtering, and pagination.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM predictions WHERE 1=1'
    params = []

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


def get_dashboard_stats():
    """
    Dynamically computes dashboard metrics from stored prediction records.
    Returns 0 and empty lists if no records exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total counts
    cursor.execute('SELECT COUNT(*) FROM predictions')
    total_applications = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM predictions WHERE prediction = 1')
    total_approved = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM predictions WHERE prediction = 0')
    total_rejected = cursor.fetchone()[0]

    approval_rate = round((total_approved / total_applications * 100), 1) if total_applications > 0 else 0.0

    # Recent 5 predictions
    cursor.execute('SELECT * FROM predictions ORDER BY id DESC LIMIT 5')
    recent_rows = cursor.fetchall()
    recent_predictions = [dict(r) for r in recent_rows]

    # Activity chart data: applications grouped by date (or Property Area if all on same day)
    cursor.execute('''
        SELECT DATE(created_at) as pred_date,
               SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as approved,
               SUM(CASE WHEN prediction = 0 THEN 1 ELSE 0 END) as rejected,
               COUNT(*) as total
        FROM predictions
        GROUP BY DATE(created_at)
        ORDER BY pred_date ASC
        LIMIT 7
    ''')
    activity_rows = cursor.fetchall()
    activity_data = {
        'dates': [r['pred_date'] for r in activity_rows],
        'approved': [r['approved'] for r in activity_rows],
        'rejected': [r['rejected'] for r in activity_rows]
    }

    # Property Area breakdown
    cursor.execute('''
        SELECT property_area,
               SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) as approved,
               SUM(CASE WHEN prediction = 0 THEN 1 ELSE 0 END) as rejected
        FROM predictions
        GROUP BY property_area
    ''')
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


def delete_prediction(app_id):
    """Deletes a single prediction record by Application ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM predictions WHERE application_id = ?', (app_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def clear_history():
    """Clears all records from the predictions table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM predictions')
    conn.commit()
    conn.close()


def export_predictions_csv():
    """Generates a CSV string of all stored predictions for file download."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM predictions ORDER BY id DESC')
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
        'Predicted Status', 'Approval Probability (%)', 'Risk Level'
    ])

    for r in rows:
        status_text = 'Approved' if r['prediction'] == 1 else 'Rejected'
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
            r['risk_level']
        ])

    return output.getvalue()


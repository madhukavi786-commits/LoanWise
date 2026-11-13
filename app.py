"""
LoanWise - Smart Customer Loan Approval Prediction System
Flask Full-Stack Web Application with Machine Learning Pipeline,
Role-Based Access Control, Explainable AI, EMI Calculator & PDF Reporting.
"""

import os
import json
import joblib
import pandas as pd
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, Response, session, jsonify
)

from preprocessing import (
    FEATURE_COLUMNS,
    format_input_dataframe,
    compute_feature_contributions
)
from database.db import (
    init_db,
    create_user,
    authenticate_user,
    get_user_by_id,
    get_all_users,
    update_user_profile,
    insert_prediction,
    get_prediction_by_id,
    get_all_predictions,
    count_predictions,
    get_dashboard_stats,
    get_risk_analytics_stats,
    delete_prediction,
    clear_history,
    export_predictions_csv
)
from utils.calculator import calculate_emi, calculate_loan_eligibility
from utils.suggestions import generate_underwriting_insights
from utils.pdf_generator import generate_loan_report_pdf

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'loanwise_fintech_production_secret_key_2026')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'loan_model.joblib')
METRICS_PATH = os.path.join(BASE_DIR, 'model', 'metrics.json')

# Global Model & Metrics references
MODEL = None
METRICS = None


def load_model_and_metrics():
    """Loads the trained ML model and evaluation metrics, auto-training if missing."""
    global MODEL, METRICS
    try:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(METRICS_PATH):
            print("[WARN] Model or metrics not found. Triggering automated training pipeline...")
            from train_model import train_and_evaluate
            train_and_evaluate()

        MODEL = joblib.load(MODEL_PATH)
        with open(METRICS_PATH, 'r') as f:
            METRICS = json.load(f)
        print("[SUCCESS] Machine Learning Model and Metrics loaded successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to load model or metrics: {e}")
        MODEL = None
        METRICS = None


# Initialize DB and Model on app boot
with app.app_context():
    init_db()
    load_model_and_metrics()


# =====================================================================
# AUTHENTICATION DECORATORS & CONTEXT PROCESSOR
# =====================================================================

def login_required(f):
    """Restricts route access to authenticated users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access this feature.", "warning")
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Restricts route access strictly to users with the 'admin' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Administrator login required.", "warning")
            return redirect(url_for('login', next=request.path))
        if session.get('role') != 'admin':
            flash("Access denied: Administrator privileges required.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_global_vars():
    """Injects global template context across all rendered views."""
    user_info = None
    if 'user_id' in session:
        user_info = {
            'id': session['user_id'],
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'role': session.get('role', 'customer')
        }
    return {
        'current_user': user_info,
        'current_year': datetime.now().year,
        'model_status': 'Operational' if MODEL is not None else 'Offline'
    }


# =====================================================================
# AUTHENTICATION ROUTES
# =====================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User Sign-In page and authentication handler."""
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return render_template('login.html')

    username_or_email = request.form.get('username_or_email', '').strip()
    password = request.form.get('password', '').strip()

    if not username_or_email or not password:
        flash("Please enter both username/email and password.", "warning")
        return render_template('login.html')

    user = authenticate_user(username_or_email, password)
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['email'] = user['email']
        session['full_name'] = user['full_name']
        session['role'] = user['role']
        flash(f"Welcome back, {user['full_name']}!", "success")

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('dashboard'))

    flash("Invalid credentials. Please verify your login details.", "danger")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User Registration page and account creation handler."""
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return render_template('register.html')

    full_name = request.form.get('full_name', '').strip()
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    role = request.form.get('role', 'customer').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not full_name or not username or not email or not password:
        flash("All fields marked with an asterisk are required.", "warning")
        return render_template('register.html')

    if len(password) < 6:
        flash("Password must be at least 6 characters long.", "warning")
        return render_template('register.html')

    if password != confirm_password:
        flash("Passwords do not match. Please re-enter.", "warning")
        return render_template('register.html')

    try:
        user_id = create_user(username, email, full_name, password, role=role)
        # Automatically establish user session
        session['user_id'] = user_id
        session['username'] = username.lower()
        session['email'] = email.lower()
        session['full_name'] = full_name
        session['role'] = 'admin' if role == 'admin' else 'customer'

        flash(f"Account created successfully! Welcome to LoanWise, {full_name}.", "success")
        return redirect(url_for('dashboard'))
    except ValueError as ve:
        flash(str(ve), "danger")
        return render_template('register.html')
    except Exception as e:
        flash(f"Registration failed: {e}", "danger")
        return render_template('register.html')


@app.route('/logout')
def logout():
    """Logs out the active session."""
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    """User profile management and personal portfolio statistics."""
    user_id = session['user_id']
    user = get_user_by_id(user_id)

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_new = request.form.get('confirm_new_password', '').strip()

        if new_password and new_password != confirm_new:
            flash("New passwords do not match.", "warning")
            return redirect(url_for('user_profile'))

        try:
            update_user_profile(user_id, full_name, email, new_password if new_password else None)
            session['full_name'] = full_name
            session['email'] = email
            flash("Profile updated successfully!", "success")
            return redirect(url_for('user_profile'))
        except ValueError as ve:
            flash(str(ve), "danger")
        except Exception as e:
            flash(f"Error updating profile: {e}", "danger")

    # Compute personal stats
    personal_preds = get_all_predictions(user_id=user_id)
    approved_cnt = sum(1 for p in personal_preds if p['prediction'] == 1)
    rejected_cnt = sum(1 for p in personal_preds if p['prediction'] == 0)

    user_stats = {
        'total': len(personal_preds),
        'approved': approved_cnt,
        'rejected': rejected_cnt
    }

    return render_template('profile.html', user=user, user_stats=user_stats)


# =====================================================================
# FEATURE 1: EMI & LOAN ELIGIBILITY CALCULATOR
# =====================================================================

@app.route('/emi-calculator')
def emi_calculator_route():
    """Interactive EMI Calculator and FOIR Loan Eligibility Estimator."""
    return render_template('emi_calculator.html')


@app.route('/api/calculate-emi', methods=['POST'])
def api_calculate_emi():
    """REST endpoint for asynchronous EMI and eligibility calculations."""
    data = request.get_json() or {}
    principal = float(data.get('principal', 150000))
    rate = float(data.get('annual_rate', 9.5))
    tenure = int(data.get('tenure_months', 360))

    emi_data = calculate_emi(principal, rate, tenure)
    return jsonify(emi_data)


# =====================================================================
# DASHBOARD ROUTE
# =====================================================================

@app.route('/')
def dashboard():
    """Executive Dashboard with dynamic portfolio KPIs from SQLite database."""
    user_id = session.get('user_id')
    is_admin = (session.get('role') == 'admin')
    filter_user_id = user_id if (user_id and not is_admin) else None

    # Customers see their own portfolio stats; admin/guest sees global portfolio
    stats = get_dashboard_stats(user_id=filter_user_id, is_admin=is_admin)
    return render_template('dashboard.html', stats=stats)


# =====================================================================
# FEATURE 2 & 3: NEW LOAN PREDICTION & EXPLAINABLE AI
# =====================================================================

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    """Customer Loan Application Form and ML Inference Pipeline."""
    global MODEL
    if request.method == 'GET':
        return render_template('predict.html')

    if MODEL is None:
        load_model_and_metrics()
        if MODEL is None:
            flash("Error: Machine Learning Model could not be loaded. Please ensure train_model.py has run.", "danger")
            return redirect(url_for('predict'))

    try:
        # Form Data Extraction
        applicant_name = request.form.get('applicant_name', '').strip()
        if not applicant_name:
            applicant_name = session.get('full_name') or 'Applicant'

        gender = request.form.get('gender', 'Male')
        married = request.form.get('married', 'No')
        dependents = request.form.get('dependents', '0')
        education = request.form.get('education', 'Graduate')
        self_employed = request.form.get('self_employed', 'No')
        applicant_income = float(request.form.get('applicant_income', 0))
        coapplicant_income = float(request.form.get('coapplicant_income', 0))
        loan_amount = float(request.form.get('loan_amount', 0))
        loan_amount_term = float(request.form.get('loan_amount_term', 360))
        credit_history = float(request.form.get('credit_history', 1.0))
        property_area = request.form.get('property_area', 'Urban')

        # Business Input Validation
        if applicant_income <= 0 and coapplicant_income <= 0:
            flash("Validation Error: Combined monthly income must be greater than zero.", "warning")
            return render_template('predict.html', form_data=request.form)

        if loan_amount <= 0:
            flash("Validation Error: Loan amount must be greater than zero (in thousands).", "warning")
            return render_template('predict.html', form_data=request.form)

        if loan_amount_term <= 0:
            flash("Validation Error: Loan term must be a positive number of months.", "warning")
            return render_template('predict.html', form_data=request.form)

        # Build feature dictionary for preprocessing
        input_data = {
            'applicant_income': applicant_income,
            'coapplicant_income': coapplicant_income,
            'loan_amount': loan_amount,
            'loan_amount_term': loan_amount_term,
            'gender': gender,
            'married': married,
            'dependents': dependents,
            'education': education,
            'self_employed': self_employed,
            'credit_history': credit_history,
            'property_area': property_area
        }

        # Convert to DataFrame matching pipeline requirements
        df_input = format_input_dataframe(input_data)

        # Run Model Inference
        raw_pred = int(MODEL.predict(df_input)[0])
        prob_approved = float(MODEL.predict_proba(df_input)[0][1])

        # Determine Risk Level Category
        if raw_pred == 1:
            if prob_approved >= 0.75:
                risk_level = "Low Risk (Prime Eligibility)"
            else:
                risk_level = "Moderate Risk (Conditional Approval)"
        else:
            if prob_approved >= 0.35:
                risk_level = "Moderate Risk (Borderline Evaluation)"
            else:
                risk_level = "High Risk (Unfavorable Underwriting Metrics)"

        # Calculate standard EMI at benchmark 9.5% p.a.
        principal_dollars = loan_amount * 1000.0
        calculated_emi = calculate_emi(principal_dollars, 9.5, loan_amount_term)

        # Save record into SQLite database with user association
        db_record = {
            'applicant_name': applicant_name,
            'gender': gender,
            'married': married,
            'dependents': dependents,
            'education': education,
            'self_employed': self_employed,
            'applicant_income': applicant_income,
            'coapplicant_income': coapplicant_income,
            'loan_amount': loan_amount,
            'loan_amount_term': loan_amount_term,
            'credit_history': credit_history,
            'property_area': property_area,
            'prediction': raw_pred,
            'probability': prob_approved,
            'risk_level': risk_level,
            'emi_amount': calculated_emi.get('emi', 0.0),
            'interest_rate': 9.5,
            'user_id': session.get('user_id')
        }
        app_id = insert_prediction(db_record, user_id=session.get('user_id'))

        flash(f"Application {app_id} evaluated successfully!", "success")
        return redirect(url_for('prediction_result', application_id=app_id))

    except ValueError as ve:
        flash(f"Input Format Error: Please verify numerical fields are filled correctly. ({ve})", "danger")
        return render_template('predict.html', form_data=request.form)
    except Exception as e:
        flash(f"Prediction Error: An unexpected error occurred: {e}", "danger")
        return render_template('predict.html', form_data=request.form)


@app.route('/result/<application_id>')
def prediction_result(application_id):
    """Visual result card with Explainable AI (XAI) feature impact, strengths, and suggestions."""
    record = get_prediction_by_id(application_id)
    if not record:
        flash(f"Application record '{application_id}' not found.", "warning")
        return redirect(url_for('history'))

    # Reconstruct input dataframe for feature explanations
    df_input = format_input_dataframe(record)
    contributions = compute_feature_contributions(MODEL, df_input) if MODEL else {}

    # Feature 3: Actionable Loan Improvement Suggestions & Strengths
    insights = generate_underwriting_insights(
        record,
        record.get('prediction', 0),
        record.get('probability', 0.5)
    )

    # Feature 1: EMI breakdown
    principal_dollars = float(record.get('loan_amount', 0)) * 1000.0
    term_months = float(record.get('loan_amount_term', 360))
    emi_calc = calculate_emi(principal_dollars, record.get('interest_rate', 9.5), term_months)

    return render_template(
        'result.html',
        record=record,
        contributions=contributions,
        insights=insights,
        emi_calc=emi_calc
    )


# =====================================================================
# FEATURE 4: DOWNLOADABLE PDF LOAN REPORT
# =====================================================================

@app.route('/report/<application_id>/download')
def download_report(application_id):
    """Generates and streams a professional PDF loan evaluation report."""
    record = get_prediction_by_id(application_id)
    if not record:
        flash(f"Application record '{application_id}' not found for PDF export.", "warning")
        return redirect(url_for('history'))

    # Customer security check: customers can only download their own reports
    if session.get('role') != 'admin' and record.get('user_id') and session.get('user_id'):
        if record['user_id'] != session['user_id']:
            flash("Access denied: You may only download reports for your own applications.", "danger")
            return redirect(url_for('history'))

    # Feature contributions for XAI in PDF
    df_input = format_input_dataframe(record)
    contributions = compute_feature_contributions(MODEL, df_input) if MODEL else None

    pdf_bytes = generate_loan_report_pdf(record, contributions=contributions)
    filename = f"LoanWise_Report_{application_id}.pdf"

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


# =====================================================================
# FEATURE 5: ADVANCED APPLICATION MANAGEMENT (HISTORY)
# =====================================================================

@app.route('/history')
def history():
    """Prediction History with real-time search, status filtering, sorting, and role isolation."""
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'all').strip()
    sort_order = request.args.get('sort', 'desc').strip()

    # Role-based data isolation:
    # Customers see only their records; Admins see all organization records
    user_id = session.get('user_id')
    is_admin = (session.get('role') == 'admin')
    filter_user_id = user_id if (user_id and not is_admin) else None

    predictions = get_all_predictions(
        search=search_query if search_query else None,
        status_filter=status_filter if status_filter != 'all' else None,
        sort_order=sort_order,
        user_id=filter_user_id
    )

    return render_template(
        'history.html',
        predictions=predictions,
        search_query=search_query,
        status_filter=status_filter,
        sort_order=sort_order,
        total_records=len(predictions)
    )


@app.route('/delete-prediction/<application_id>', methods=['POST'])
@login_required
def delete_prediction_route(application_id):
    """Deletes a single prediction record with role authorization."""
    user_id = session.get('user_id')
    is_admin = (session.get('role') == 'admin')

    deleted = delete_prediction(application_id, user_id=user_id, is_admin=is_admin)
    if deleted:
        flash(f"Record '{application_id}' deleted successfully.", "info")
    else:
        flash(f"Record '{application_id}' could not be deleted or does not exist.", "warning")
    return redirect(url_for('history'))


@app.route('/clear-history', methods=['POST'])
@admin_required
def clear_history_route():
    """Clears all records from the predictions table (Administrator only)."""
    clear_history(is_admin=True)
    flash("Application database history has been cleared.", "info")
    return redirect(url_for('history'))


@app.route('/export-history')
def export_history_route():
    """Exports stored prediction records as a downloadable CSV file."""
    user_id = session.get('user_id')
    is_admin = (session.get('role') == 'admin')

    csv_data = export_predictions_csv(user_id=user_id, is_admin=is_admin)
    filename = f"loanwise_prediction_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


# =====================================================================
# FEATURE 6: RISK ANALYSIS DASHBOARD
# =====================================================================

@app.route('/analytics')
def risk_analytics():
    """Risk Analysis Dashboard: Distribution charts, risk tiers, and income breakdowns."""
    user_id = session.get('user_id')
    is_admin = (session.get('role') == 'admin')

    analytics_stats = get_risk_analytics_stats(user_id=user_id, is_admin=is_admin)
    return render_template('analytics.html', stats=analytics_stats)


# =====================================================================
# MODEL PERFORMANCE & MODEL INSIGHTS ROUTES
# =====================================================================

@app.route('/performance')
def performance():
    """Displays actual model evaluation results from holdout test set."""
    global METRICS
    if METRICS is None and os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, 'r') as f:
            METRICS = json.load(f)

    return render_template('performance.html', metrics=METRICS)


@app.route('/insights')
def insights():
    """Model Insights: Logistic regression coefficients, feature weights, and distributions."""
    global METRICS
    if METRICS is None and os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, 'r') as f:
            METRICS = json.load(f)

    return render_template('insights.html', metrics=METRICS)


@app.route('/seed-demo-data', methods=['POST'])
def seed_demo_data():
    """Helper route to populate 4 realistic sample loan records for review demonstration."""
    sample_applicants = [
        {
            'applicant_name': 'Eleanor Vance',
            'gender': 'Female',
            'married': 'Yes',
            'dependents': '1',
            'education': 'Graduate',
            'self_employed': 'No',
            'applicant_income': 6200.0,
            'coapplicant_income': 2400.0,
            'loan_amount': 160.0,
            'loan_amount_term': 360.0,
            'credit_history': 1.0,
            'property_area': 'Semiurban',
            'prediction': 1,
            'probability': 0.892,
            'risk_level': 'Low Risk (Prime Eligibility)',
            'emi_amount': 1345.36,
            'interest_rate': 9.5,
            'user_id': session.get('user_id')
        },
        {
            'applicant_name': 'Marcus Brody',
            'gender': 'Male',
            'married': 'No',
            'dependents': '0',
            'education': 'Not Graduate',
            'self_employed': 'Yes',
            'applicant_income': 2800.0,
            'coapplicant_income': 0.0,
            'loan_amount': 195.0,
            'loan_amount_term': 360.0,
            'credit_history': 0.0,
            'property_area': 'Rural',
            'prediction': 0,
            'probability': 0.041,
            'risk_level': 'High Risk (Unfavorable Underwriting Metrics)',
            'emi_amount': 1639.66,
            'interest_rate': 9.5,
            'user_id': session.get('user_id')
        },
        {
            'applicant_name': 'Devon Patel',
            'gender': 'Male',
            'married': 'Yes',
            'dependents': '2',
            'education': 'Graduate',
            'self_employed': 'No',
            'applicant_income': 5400.0,
            'coapplicant_income': 1800.0,
            'loan_amount': 140.0,
            'loan_amount_term': 360.0,
            'credit_history': 1.0,
            'property_area': 'Urban',
            'prediction': 1,
            'probability': 0.824,
            'risk_level': 'Low Risk (Prime Eligibility)',
            'emi_amount': 1177.19,
            'interest_rate': 9.5,
            'user_id': session.get('user_id')
        },
        {
            'applicant_name': 'Sarah Connor',
            'gender': 'Female',
            'married': 'No',
            'dependents': '1',
            'education': 'Graduate',
            'self_employed': 'Yes',
            'applicant_income': 4100.0,
            'coapplicant_income': 1200.0,
            'loan_amount': 210.0,
            'loan_amount_term': 180.0,
            'credit_history': 1.0,
            'property_area': 'Rural',
            'prediction': 1,
            'probability': 0.685,
            'risk_level': 'Moderate Risk (Conditional Approval)',
            'emi_amount': 2192.65,
            'interest_rate': 9.5,
            'user_id': session.get('user_id')
        }
    ]

    for record in sample_applicants:
        insert_prediction(record, user_id=session.get('user_id'))

    flash("Seeded 4 realistic demonstration applications successfully!", "success")
    return redirect(url_for('dashboard'))


# =====================================================================
# ERROR HANDLERS
# =====================================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', error_title="404 - Page Not Found",
                           error_message="The requested URL was not found on the LoanWise server."), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', error_title="500 - Server Error",
                           error_message="An internal server error occurred. Please check console logs."), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print("   LOANWISE: Smart Customer Loan Approval Prediction System")
    print(f"   Server running at: http://0.0.0.0:{port}")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=port, debug=False)

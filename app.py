"""
LoanWise - Smart Customer Loan Approval Prediction System
Flask Backend Application
"""

import os
import json
import joblib
import pandas as pd
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, Response, jsonify
)

from preprocessing import (
    FEATURE_COLUMNS,
    format_input_dataframe,
    compute_feature_contributions
)
from database.db import (
    init_db,
    insert_prediction,
    get_prediction_by_id,
    get_all_predictions,
    get_dashboard_stats,
    delete_prediction,
    clear_history,
    export_predictions_csv
)

app = Flask(__name__)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'loan_model.joblib')
METRICS_PATH = os.path.join(BASE_DIR, 'model', 'metrics.json')

# Global references
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


# Initialize DB and Model on startup
with app.app_context():
    init_db()
    load_model_and_metrics()


@app.context_processor
def inject_global_vars():
    """Injects helpful variables into all Jinja2 templates."""
    return {
        'current_year': datetime.now().year,
        'model_status': 'Operational' if MODEL is not None else 'Offline'
    }


# =====================================================================
# ROUTES
# =====================================================================

@app.route('/')
def dashboard():
    """Interactive Dashboard with dynamic statistics from SQLite database."""
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)


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
        # Form Data Extraction & Basic Sanitization
        applicant_name = request.form.get('applicant_name', 'Applicant').strip() or 'Applicant'
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

        # Business Validation
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

        # Save record into SQLite database
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
            'risk_level': risk_level
        }
        app_id = insert_prediction(db_record)

        flash(f"Application {app_id} processed successfully!", "success")
        return redirect(url_for('prediction_result', application_id=app_id))

    except ValueError as ve:
        flash(f"Input Format Error: Please verify numerical fields are filled correctly. ({ve})", "danger")
        return render_template('predict.html', form_data=request.form)
    except Exception as e:
        flash(f"Prediction Error: An unexpected error occurred: {e}", "danger")
        return render_template('predict.html', form_data=request.form)


@app.route('/result/<application_id>')
def prediction_result(application_id):
    """Detailed visual result card with Explainable AI (XAI) feature impact."""
    record = get_prediction_by_id(application_id)
    if not record:
        flash(f"Application record '{application_id}' not found.", "warning")
        return redirect(url_for('history'))

    # Reconstruct input dataframe for feature explanations
    df_input = format_input_dataframe(record)
    contributions = compute_feature_contributions(MODEL, df_input) if MODEL else {}

    return render_template(
        'result.html',
        record=record,
        contributions=contributions
    )


@app.route('/history')
def history():
    """Prediction History with real-time search, status filtering, and actions."""
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'all').strip()

    predictions = get_all_predictions(
        search=search_query if search_query else None,
        status_filter=status_filter if status_filter != 'all' else None
    )

    return render_template(
        'history.html',
        predictions=predictions,
        search_query=search_query,
        status_filter=status_filter,
        total_records=len(predictions)
    )


@app.route('/delete-prediction/<application_id>', methods=['POST'])
def delete_prediction_route(application_id):
    """Deletes a single prediction record from the database."""
    deleted = delete_prediction(application_id)
    if deleted:
        flash(f"Record '{application_id}' deleted successfully.", "info")
    else:
        flash(f"Record '{application_id}' could not be deleted or does not exist.", "warning")
    return redirect(url_for('history'))


@app.route('/clear-history', methods=['POST'])
def clear_history_route():
    """Clears all records from the predictions table."""
    clear_history()
    flash("Prediction history has been completely cleared.", "info")
    return redirect(url_for('history'))


@app.route('/export-history')
def export_history_route():
    """Exports all stored prediction records as a downloadable CSV file."""
    csv_data = export_predictions_csv()
    filename = f"loanwise_prediction_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


@app.route('/performance')
def performance():
    """Displays actual model evaluation results from real test set."""
    global METRICS
    if METRICS is None and os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, 'r') as f:
            METRICS = json.load(f)

    return render_template('performance.html', metrics=METRICS)


@app.route('/insights')
def insights():
    """Model Insights: Coefficients, feature importance, and dataset distributions."""
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
            'risk_level': 'Low Risk (Prime Eligibility)'
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
            'risk_level': 'High Risk (Unfavorable Underwriting Metrics)'
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
            'risk_level': 'Low Risk (Prime Eligibility)'
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
            'risk_level': 'Moderate Risk (Conditional Approval)'
        }
    ]

    for record in sample_applicants:
        insert_prediction(record)

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
    print("\n" + "="*60)
    print("   LOANWISE: Smart Customer Loan Approval Prediction System")
    print("   Server running at: http://127.0.0.1:5000")
    print("="*60 + "\n")
    if __name__ == '__main__':
       port = int(os.environ.get('PORT', 5000))
       app.run(host='0.0.0.0', port=port, debug=False)
from database.db import 
(
    init_db,
    insert_prediction,
    get_prediction_by_id,
    get_all_predictions
)


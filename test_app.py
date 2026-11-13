"""
LoanWise - End-to-End Automated Test Suite
Verifies all Flask routes, model inference, database persistence,
filtering, CSV export, and XAI calculations.
"""

import unittest
import os
import json
from app import app
from database.db import init_db, clear_history, get_all_predictions


class LoanWiseTestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

    def setUp(self):
        clear_history()

    def tearDown(self):
        pass

    def test_01_dashboard_empty_state(self):
        """Dashboard renders cleanly with zero records."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Underwriting Dashboard', response.data)
        self.assertIn(b'No Loan Applications Processed Yet', response.data)

    def test_02_predict_page_render(self):
        """Prediction form loads with all required fields."""
        response = self.client.get('/predict')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New Customer Loan Application', response.data)
        self.assertIn(b'applicant_income', response.data)
        self.assertIn(b'credit_history', response.data)

    def test_03_predict_prime_applicant_approval(self):
        """Prime applicant profile generates an Approved result with high probability."""
        payload = {
            'applicant_name': 'Sarah Jenkins',
            'gender': 'Female',
            'married': 'Yes',
            'dependents': '1',
            'education': 'Graduate',
            'self_employed': 'No',
            'applicant_income': '6500',
            'coapplicant_income': '2000',
            'loan_amount': '150',
            'loan_amount_term': '360',
            'credit_history': '1.0',
            'property_area': 'Semiurban'
        }
        response = self.client.post('/predict', data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'LOAN APPLICATION APPROVED', response.data)
        self.assertIn(b'Approval Confidence Probability', response.data)
        self.assertIn(b'Sarah Jenkins', response.data)
        self.assertIn(b'Advisory Machine Learning Disclaimer', response.data)

    def test_04_predict_high_risk_rejection(self):
        """High-risk applicant (unsteady, poor credit) generates a Rejection."""
        payload = {
            'applicant_name': 'Carl Grimes',
            'gender': 'Male',
            'married': 'No',
            'dependents': '0',
            'education': 'Not Graduate',
            'self_employed': 'Yes',
            'applicant_income': '2200',
            'coapplicant_income': '0',
            'loan_amount': '220',
            'loan_amount_term': '360',
            'credit_history': '0.0',
            'property_area': 'Rural'
        }
        response = self.client.post('/predict', data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'LOAN APPLICATION REJECTED', response.data)
        self.assertIn(b'Factors Increasing Risk', response.data)

    def test_05_validation_errors(self):
        """Invalid zero income and zero loan amount trigger validation error messages."""
        payload = {
            'applicant_name': 'Invalid Applicant',
            'applicant_income': '0',
            'coapplicant_income': '0',
            'loan_amount': '100',
            'loan_amount_term': '360',
            'credit_history': '1.0',
            'property_area': 'Urban'
        }
        response = self.client.post('/predict', data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Combined monthly income must be greater than zero', response.data)

    def test_06_prediction_history_and_search(self):
        """History page lists submissions and responds to filters and search."""
        # Insert a sample
        self.client.post('/predict', data={
            'applicant_name': 'Zack Taylor',
            'gender': 'Male',
            'married': 'No',
            'dependents': '0',
            'education': 'Graduate',
            'self_employed': 'No',
            'applicant_income': '5000',
            'coapplicant_income': '0',
            'loan_amount': '120',
            'loan_amount_term': '360',
            'credit_history': '1.0',
            'property_area': 'Urban'
        }, follow_redirects=True)

        # Query history
        res = self.client.get('/history')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Zack Taylor', res.data)

        # Search query
        res_search = self.client.get('/history?search=Zack')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b'Zack Taylor', res_search.data)

        # Search query with no match
        res_none = self.client.get('/history?search=NonExistentPerson')
        self.assertEqual(res_none.status_code, 200)
        self.assertIn(b'No Records Matching Criteria', res_none.data)

    def test_07_export_history_csv(self):
        """Export CSV endpoint returns proper content type and CSV header."""
        # Insert a record first
        self.client.post('/predict', data={
            'applicant_name': 'Alice Wonder',
            'gender': 'Female',
            'married': 'Yes',
            'dependents': '0',
            'education': 'Graduate',
            'self_employed': 'No',
            'applicant_income': '5500',
            'coapplicant_income': '1500',
            'loan_amount': '130',
            'loan_amount_term': '360',
            'credit_history': '1.0',
            'property_area': 'Semiurban'
        }, follow_redirects=True)

        res = self.client.get('/export-history')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/csv')
        self.assertIn('attachment;filename=loanwise_prediction_history_', res.headers.get('Content-Disposition', ''))
        self.assertIn(b'Application ID,Applicant Name', res.data)
        self.assertIn(b'Alice Wonder', res.data)

    def test_08_model_performance_page(self):
        """Performance page displays actual test-set accuracy, precision, confusion matrix."""
        res = self.client.get('/performance')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Model Evaluation &amp; Metrics', res.data)
        self.assertIn(b'86.18%', res.data)  # Actual test set accuracy
        self.assertIn(b'True Negatives (TN)', res.data)
        self.assertIn(b'Classification Report', res.data)

    def test_09_model_insights_page(self):
        """Insights page renders coefficients, feature importance, and non-causal note."""
        res = self.client.get('/insights')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Underwriting Insights &amp; Coefficients', res.data)
        self.assertIn(b'Logistic Regression Coefficients', res.data)
        self.assertIn(b'They do not establish direct causal relationships', res.data)

    def test_10_seed_demo_data(self):
        """Demo seed route populates 4 realistic applications into DB."""
        res = self.client.post('/seed-demo-data', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Seeded 4 realistic demonstration applications', res.data)
        records = get_all_predictions()
        self.assertEqual(len(records), 4)

    def test_11_user_registration_and_login(self):
        """Tests user registration, session establishment, and logout."""
        # 1. Register new customer
        reg_payload = {
            'full_name': 'Diana Prince',
            'username': 'diana',
            'email': 'diana@themyscira.com',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'role': 'customer'
        }
        res_reg = self.client.post('/register', data=reg_payload, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)
        self.assertIn(b'Account created successfully', res_reg.data)

        # 2. Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)
        self.assertIn(b'You have been signed out successfully', res_logout.data)

        # 3. Login
        login_payload = {
            'username_or_email': 'diana@themyscira.com',
            'password': 'Password@123'
        }
        res_login = self.client.post('/login', data=login_payload, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b'Welcome back, Diana Prince!', res_login.data)

    def test_12_emi_calculator_and_api(self):
        """Tests EMI calculator route and calculation API."""
        # Page render
        res_page = self.client.get('/emi-calculator')
        self.assertEqual(res_page.status_code, 200)
        self.assertIn(b'EMI &amp; Eligibility Calculator', res_page.data)

        # API endpoint
        api_payload = {
            'principal': 100000,
            'annual_rate': 10.0,
            'tenure_months': 120
        }
        res_api = self.client.post('/api/calculate-emi', json=api_payload)
        self.assertEqual(res_api.status_code, 200)
        data = res_api.get_json()
        self.assertIn('emi', data)
        self.assertGreater(data['emi'], 1000)
        self.assertIn('total_interest', data)

    def test_13_pdf_report_download(self):
        """Tests downloading official PDF loan report."""
        # Submit an application
        self.client.post('/predict', data={
            'applicant_name': 'Bruce Wayne',
            'gender': 'Male',
            'married': 'No',
            'dependents': '0',
            'education': 'Graduate',
            'self_employed': 'Yes',
            'applicant_income': '12000',
            'coapplicant_income': '0',
            'loan_amount': '300',
            'loan_amount_term': '360',
            'credit_history': '1.0',
            'property_area': 'Urban'
        }, follow_redirects=True)

        records = get_all_predictions()
        self.assertGreater(len(records), 0)
        app_id = records[0]['application_id']

        # Download report
        res_pdf = self.client.get(f'/report/{app_id}/download')
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.mimetype, 'application/pdf')
        self.assertIn(f'attachment;filename=LoanWise_Report_{app_id}.pdf', res_pdf.headers.get('Content-Disposition', ''))
        self.assertGreater(len(res_pdf.data), 1000)

    def test_14_risk_analytics_dashboard(self):
        """Tests Risk Analytics page rendering and metrics."""
        res_analytics = self.client.get('/analytics')
        self.assertEqual(res_analytics.status_code, 200)
        self.assertIn(b'Risk Analytics &amp; Portfolio Intelligence', res_analytics.data)
        self.assertIn(b'Methodological Notice', res_analytics.data)

    def test_15_underwriting_suggestions_and_strengths(self):
        """Tests that result view provides XAI factor attribution and improvement suggestions."""
        res = self.client.post('/predict', data={
            'applicant_name': 'Barry Allen',
            'gender': 'Male',
            'married': 'No',
            'dependents': '0',
            'education': 'Graduate',
            'self_employed': 'No',
            'applicant_income': '4500',
            'coapplicant_income': '0',
            'loan_amount': '110',
            'loan_amount_term': '360',
            'credit_history': '1.0',
            'property_area': 'Semiurban'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Explainable AI (XAI)', res.data)
        self.assertIn(b'Actionable Loan Improvement Suggestions', res.data)
        self.assertIn(b'Download Official PDF Report', res.data)


if __name__ == '__main__':
    unittest.main()


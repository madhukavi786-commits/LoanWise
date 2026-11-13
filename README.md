# LoanWise – Smart Customer Loan Approval Prediction System
### FinTech Machine Learning Underwriting Platform & Portfolio Intelligence

> **A Production-Grade Full-Stack Machine Learning Web Application**  
> Developed for Academic Internship Final Review &amp; FinTech Industry Portfolio Showcase.  
> **Live Deployment:** [https://loanwise-prwj.onrender.com](https://loanwise-prwj.onrender.com)  
> **Repository:** [https://github.com/madhukavi786-commits/LoanWise](https://github.com/madhukavi786-commits/LoanWise)

---

## 1. Executive Overview

**LoanWise** is a full-stack, enterprise-grade loan underwriting platform that combines statistical Machine Learning with Explainable AI (XAI), financial mathematics, and role-based portfolio management. Powered by a trained **Scikit-Learn Logistic Regression Pipeline** and **ColumnTransformer**, the system ingests 11 demographic, cashflow, and credit criteria to generate instant automated loan eligibility decisions, probabilistic confidence scores, and multi-factor risk attribution.

The platform includes an **interactive EMI calculator**, **FOIR borrowing capacity modeling**, **official downloadable PDF loan reports**, an **advanced risk analytics dashboard**, and **secure role-based authentication** (Admin &amp; Customer).

---

## 2. Comprehensive Technology Stack

| Layer | Technologies &amp; Libraries | Purpose |
| :--- | :--- | :--- |
| **Backend &amp; API** | Python 3.10+ &bull; Flask &bull; Gunicorn | Application microframework, session management, REST endpoints, WSGI serving |
| **Machine Learning** | Scikit-Learn &bull; Pandas &bull; NumPy | Logistic Regression, ColumnTransformer, SimpleImputer, StandardScaler, OneHotEncoder |
| **Model Persistence** | Joblib &bull; JSON | Artifact serialization, deserialization, and evaluation metrics storage |
| **Security &amp; Auth** | Werkzeug Security | PBKDF2 password hashing, role-based decorators (`@login_required`, `@admin_required`) |
| **Database** | SQLite3 | ACID-compliant persistence for users, application logs, and portfolio metrics |
| **Financial Math** | Standard Banking Formulas | Equated Monthly Installment (EMI) and 50% FOIR eligibility estimation |
| **Reporting Engine** | ReportLab (v5.1.0) | Automated multi-section PDF underwriting report generation |
| **Frontend UI/UX** | HTML5, CSS3, Bootstrap 5, Chart.js | Modern FinTech design system with Deep Navy (#101B35) &amp; Primary Blue (#2563EB) |

---

## 3. Seven Core Feature Upgrades

### Feature 1: EMI &amp; Borrowing Eligibility Calculator (`/emi-calculator`)
- **Standard Banking EMI Formula**:
  $$E = P \cdot r \cdot \frac{(1+r)^n}{(1+r)^n - 1}$$
  Calculates monthly installments, total interest burden, and total repayment amount.
- **Visual Breakdown**: Interactive **Chart.js** doughnut chart displaying principal vs. interest breakdown in real time.
- **Fixed Obligation to Income Ratio (FOIR) Estimator**: Models borrowing capacity up to the institutional 50% debt-service ceiling based on net earnings and existing liabilities.

### Feature 2: Explainable AI (XAI) – Why This Decision?
- Extracts individual log-odds contributions ($\beta_i \cdot x_i$) from trained Logistic Regression weights.
- Deconstructs the decision into:
  - **Factors Supporting Approval** (positive coefficients shifting boundary toward eligibility).
  - **Factors Increasing Risk** (negative weights depressing approval odds).
  - **Applicant Financial Strengths** (e.g., dual-income buffer, graduate qualification, low loan-to-income multiplier).
  - **Underwriting Risk Indicators** (e.g., adverse credit history, high dependents, single income).
- Explicit disclaimer separating model advisory predictions from legally binding credit approvals.

### Feature 3: Actionable Loan Improvement Suggestions
- Generates data-driven roadmaps to guide rejected or borderline applicants toward future eligibility:
  - Rebuilding credit rating and removing derogatory marks.
  - Adjusting requested principal or extending tenure to lower monthly debt pressure.
  - Adding an earning co-applicant to pool qualifying household income.
  - Verifying self-employment cashflow records.
  - Disclaimer: Recommendations do not guarantee future credit approval.

### Feature 4: Downloadable Official PDF Loan Report
- Generates a styled, branded underwriting summary report via **ReportLab**:
  - Executive decision banner (Approved / Rejected) with risk tier.
  - Tabular breakdown of applicant demographics, income, and requested terms.
  - EMI and repayment schedule summary.
  - Top positive and negative Explainable AI factors.
  - Actionable improvement suggestions.
  - Timestamp, application reference code, and regulatory compliance disclaimer.
- Direct endpoint: `/report/<application_id>/download`.

### Feature 5: Advanced Application Management (Audit Register)
- **Role-Based Data Isolation**:
  - **Customer**: Inspects exclusively their personal application submissions.
  - **Administrator**: Oversees the entire institutional portfolio.
- **Real-Time Filtering &amp; Search**: Query by Applicant Name, Application ID, Education, or Property Area.
- **Sorting**: Toggle between newest submissions and oldest records.
- **CSV Data Export**: Download complete database logs via `/export-history`.

### Feature 6: Risk Analysis Dashboard (`/analytics`)
- Dynamic portfolio visualizations powered by actual database records:
  - Total volume, approved volume, rejected volume, and approval percentage.
  - **Risk Tier Distribution**: Low Risk (Prime), Moderate Risk (Borderline), High Risk (Unfavorable).
  - **Income Distribution vs. Approval Ratio**: (<$2.5k, $2.5k-$5k, $5k-$10k, >$10k).
  - **Credit History Outcomes**: 1.0 Guideline compliant vs. 0.0 Adverse.
  - **Loan Request Size Brackets**: (<$100k, $100k-$200k, $200k-$300k, >$300k).
  - Methodological notice clarifying that risk reflects **predicted underwriting risk** rather than realized post-disbursal default history.

### Feature 7: User Authentication &amp; Role-Based Access Control
- Secure user registration and login with **Werkzeug** PBKDF2 password hashing.
- Role management (`admin` and `customer`).
- Session protection on administrative features and personal history views.
- User profile page (`/profile`) with credential updating and personal stats.

---

## 4. Pre-Seeded Demonstration Accounts

For review evaluations and demonstration sessions, default accounts are pre-seeded in the database:

| Role | Username / Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` &bull; `admin@loanwise.com` | `Admin@123` | Full access: all applications, global analytics, delete/clear |
| **Customer** | `customer` &bull; `customer@loanwise.com` | `Customer@123` | Personal applications, submission form, own reports |

---

## 5. Project Directory Structure

```text
internpro/
├── app.py                     # Flask controllers, routes, sessions & decorators
├── train_model.py             # Model training, stratified validation & metric exports
├── preprocessing.py           # ColumnTransformer pipeline, imputers, scalers & XAI
├── requirements.txt           # Production Python dependencies (includes ReportLab)
├── test_app.py                # 15 automated unit & integration tests
├── README.md                  # Comprehensive technical documentation
├── run_loanwise.bat           # 1-Click Windows Batch launcher
├── run.ps1                    # 1-Click PowerShell launcher
├── utils/
│   ├── __init__.py            # Package initializer
│   ├── calculator.py          # Standard EMI & FOIR eligibility algorithms
│   ├── suggestions.py         # Underwriting insights, strengths & advisory rules
│   └── pdf_generator.py       # ReportLab PDF report generation engine
├── dataset/
│   └── loan_data.csv          # Real Kaggle loan dataset (614 rows, 11 features)
├── model/
│   ├── loan_model.joblib      # Serialized scikit-learn pipeline (Joblib)
│   └── metrics.json           # Actual holdout test metrics & logistic regression weights
├── database/
│   ├── __init__.py            # Database package initializer
│   ├── db.py                  # SQLite DAO, schema queries, users & analytics
│   └── loanwise.db            # Persistent SQLite database
├── static/
│   ├── css/
│   │   └── style.css          # FinTech design system (Navy #101B35, Blue #2563EB)
│   └── js/
│       └── main.js            # Dynamic DOM handlers, client EMI calculator, demo presets
└── templates/
    ├── base.html              # Responsive base layout with collapsible sidebar
    ├── dashboard.html         # Executive overview KPIs, doughnut ratio & volume chart
    ├── predict.html           # 11-feature customer application form with validation
    ├── result.html            # Visual decision card, XAI breakdown, EMI & PDF button
    ├── emi_calculator.html    # Interactive EMI simulation & FOIR capacity modeling
    ├── analytics.html         # Risk analysis dashboard & demographic distributions
    ├── history.html           # Historical records table, search, filter, sort & CSV
    ├── performance.html       # Confusion matrix, classification report & specs
    ├── insights.html          # Feature weights & exploratory dataset charts
    ├── login.html             # FinTech sign-in card with 1-click demo chips
    ├── register.html          # Account creation card with role selection
    └── profile.html           # User profile management & personal stats
```

---

## 6. How to Run Locally

### Step 1: Open Terminal in Project Directory
```powershell
cd d:\FlutterProjects\internpro
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```
*(Or with Anaconda)*:
```powershell
& "D:\anaconda\python.exe" -m pip install -r requirements.txt
```

### Step 3: Run the Automated Test Suite (15 Tests)
```powershell
python -m unittest test_app.py -v
```
*(Or with Anaconda)*:
```powershell
& "D:\anaconda\python.exe" -m unittest test_app.py -v
```

### Step 4: Launch the Web Application
```powershell
python app.py
```
*(Or with Anaconda)*:
```powershell
& "D:\anaconda\python.exe" app.py
```
*(Or using the provided launchers)*:
```powershell
.\run.ps1
```
Open your browser at:
```text
http://127.0.0.1:5000
```

---

## 7. Render Deployment Instructions

The application is fully configured for deployment on **Render**:

1. **Build & Start Commands**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
2. **Environment Variables**:
   - `SECRET_KEY`: Set a secure random string (e.g. `loanwise_prod_secret_998124_key`).
   - `PORT`: Automatically assigned by Render.
   - `DATABASE_PATH`: (Optional) `/var/data/loanwise.db` if using a Render Persistent Disk. If using default ephemeral storage, SQLite runs seamlessly in the local `database/loanwise.db` directory.
3. **Database Persistence on Free Tier**:
   - Render's free web service tier restarts periodically, which refreshes ephemeral file storage. The database auto-initializes on startup (`init_db()`), guaranteeing zero crashes and instant accessibility. For long-term production persistence, attach a Render Persistent Disk or configure a managed database.

---

## 8. Summary of Automated Verification Results

All 15 automated test cases executed successfully via `test_app.py`:

```text
test_01_dashboard_empty_state ............................... [PASS]
test_02_predict_page_render ................................. [PASS]
test_03_predict_prime_applicant_approval .................... [PASS]
test_04_predict_high_risk_rejection ......................... [PASS]
test_05_validation_errors ................................... [PASS]
test_06_prediction_history_and_search ....................... [PASS]
test_07_export_history_csv .................................. [PASS]
test_08_model_performance_page .............................. [PASS]
test_09_model_insights_page ................................. [PASS]
test_10_seed_demo_data ...................................... [PASS]
test_11_user_registration_and_login ......................... [PASS]
test_12_emi_calculator_and_api .............................. [PASS]
test_13_pdf_report_download ................................. [PASS]
test_14_risk_analytics_dashboard ............................ [PASS]
test_15_underwriting_suggestions_and_strengths .............. [PASS]
----------------------------------------------------------------------
Ran 15 tests in 2.376s (OK)
```

# LoanWise – Smart Customer Loan Approval Prediction System

> **A Production-Grade Machine Learning Web Application for Underwriting Risk Evaluation**  
> Developed for Academic Internship Final Review &amp; Industry Portfolio Showcase.

---

## 1. Executive Summary

**LoanWise** is a full-stack, end-to-end Machine Learning web application designed to assist commercial banks and fintech lenders in assessing customer loan approval probability. Using a trained **Scikit-Learn Logistic Regression Pipeline**, the system evaluates applicant demographic, financial, and credit parameters to generate automated underwriting decisions, confidence probabilities, and Explainable AI (XAI) feature attributions.

The platform provides a financial dashboard, interactive prediction engine, persistent audit history (SQLite), test-set performance metrics, and model interpretability visualizers powered by **Chart.js**.

---

## 2. Technology Stack

| Domain | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Backend** | Python 3.10+ / Flask | Microframework, routing, REST endpoints, session handling |
| **Machine Learning** | Scikit-Learn | Logistic Regression, Pipeline, ColumnTransformer, metrics |
| **Data Processing** | Pandas, NumPy | DataFrame manipulation, statistical aggregations |
| **Model Persistence** | Joblib | Serialization and fast deserialization of pipeline |
| **Database** | SQLite3 | Audit trail storage, application tracking, dynamic KPIs |
| **Frontend UI/UX** | HTML5, CSS3, Bootstrap 5 | Responsive fintech UI (Navy blue, white, light grey) |
| **Data Visualization**| Chart.js (v4.4.1) | Interactive doughnut, bar, and horizontal coefficient charts |
| **Icons & Typography**| Bootstrap Icons & Plus Jakarta Sans | Modern typography and iconography |

---

## 3. Machine Learning Architecture

### 3.1 Dataset Benchmark
The model is trained on the authentic **Loan Prediction Dataset** (Kaggle / Analytics Vidhya benchmark, 614 applicant records):
- **11 Predictor Features**:
  - **Numerical**: `ApplicantIncome`, `CoapplicantIncome`, `LoanAmount`, `Loan_Amount_Term`
  - **Categorical**: `Gender`, `Married`, `Dependents`, `Education`, `Self_Employed`, `Credit_History`, `Property_Area`
- **Target Variable**: `Loan_Status` (`Y` = Approved / 1, `N` = Rejected / 0)

### 3.2 Data Leakage Prevention
To guarantee rigorous generalization, all transformations are encapsulated inside a **Scikit-Learn `ColumnTransformer`**:
- **Numerical Pipeline**: Median Imputation (`SimpleImputer`) $\rightarrow$ Feature Standardization (`StandardScaler`).
- **Categorical Pipeline**: Most-Frequent Imputation (`SimpleImputer`) $\rightarrow$ One-Hot Encoding (`OneHotEncoder(handle_unknown='ignore')`).
- **Splitting Strategy**: 80/20 Stratified Train-Test split (`random_state=42`) preserves minority class proportions.

### 3.3 Evaluation Metrics (Actual Holdout Test Set)
- **Accuracy**: `86.18%`
- **Precision (Approved Class)**: `84.00%`
- **Recall (Approved Class)**: `98.82%`
- **F1-Score**: `90.81%`
- **ROC-AUC**: `85.26%`
- **Confusion Matrix**: `TN=22`, `FP=16`, `FN=1`, `TP=84`

---

## 4. Project Directory Structure

```text
internpro/
├── app.py                     # Main Flask web application and routing controllers
├── train_model.py             # ML training, stratified validation, and metric generation
├── preprocessing.py           # Reusable ColumnTransformer pipelines & XAI calculations
├── requirements.txt           # Project Python dependencies
├── README.md                  # Comprehensive technical documentation
├── dataset/
│   └── loan_data.csv          # Real benchmark loan applicant dataset (614 rows)
├── model/
│   ├── loan_model.joblib      # Serialized scikit-learn pipeline artifact
│   └── metrics.json           # Actual holdout test metrics, confusion matrix, & weights
├── database/
│   ├── __init__.py            # Database package initializer
│   ├── db.py                  # SQLite DAO, schema queries, dynamic stats, & CSV exporter
│   └── loanwise.db            # Persistent SQLite database file
├── static/
│   ├── css/
│   │   └── style.css          # Fintech design system (navy blue, cards, badges)
│   └── js/
│       └── main.js            # Frontend scripts, preset demo profiles, & form handlers
└── templates/
    ├── base.html              # Responsive layout template with navigation sidebar
    ├── dashboard.html         # Portfolio KPIs, doughnut ratio, & activity charts
    ├── predict.html           # 11-feature customer application form with validation
    ├── result.html            # Visual decision card, confidence meter, & XAI attribution
    ├── history.html           # Historical records table, real-time search, & CSV export
    ├── performance.html       # Confusion matrix, classification report, & model specs
    └── insights.html          # Logistic regression coefficients & dataset distributions
```

---

## 5. Quick Start & Execution Guide

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed.
- PowerShell or Command Prompt.

### Step 1: Clone or Navigate to Project Directory
```powershell
cd d:\FlutterProjects\internpro
```

### Step 2: (Optional) Create & Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```
*(If using Anaconda directly)*:
```powershell
& "D:\anaconda\python.exe" -m pip install -r requirements.txt
```

### Step 4: Train Model & Build Artifacts
Run the dedicated training script to train the Logistic Regression pipeline and compute evaluation metrics:
```powershell
python train_model.py
```
*(Or with Anaconda)*:
```powershell
& "D:\anaconda\python.exe" train_model.py
```

### Step 5: Launch the LoanWise Web Application
```powershell
python app.py
```
*(Or with Anaconda)*:
```powershell
& "D:\anaconda\python.exe" app.py
```

Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 6. Application Tour & Features

### 1. Underwriting Dashboard (`/`)
- Dynamic statistics calculated directly from SQLite records (Total Applications, Total Approved, Total Rejected, Approval Rate %).
- Dynamic **Approval vs. Rejection Doughnut Chart** (Chart.js).
- Dynamic **Application Activity Trend Chart** (Chart.js).
- Clean empty states when database is fresh, with a 1-click **"Seed Demo Data"** button for fast demonstration during reviews.

### 2. New Customer Loan Application Form (`/predict`)
- 11 underwriting fields logically partitioned into 3 sections:
  1. *Personal & Demographic Profile* (Gender, Marital Status, Dependents, Education, Self-Employed).
  2. *Financial Parameters* (Applicant Income, Co-applicant Income, Loan Amount, Term Duration).
  3. *Credit & Collateral Criteria* (Credit Bureau History 1.0/0.0, Property Area).
- **Interactive Quick-Fill Archetypes**:
  - **Prime Applicant Profile**: Graduate, Married, $6,500 income, Good credit history (Triggers Approval ~89%).
  - **High-Risk Profile**: Delinquent credit, $2,400 income, high loan request (Triggers Rejection ~96%).
  - **Moderate Co-App Profile**: Demonstrates co-applicant balancing effect.
- Instant client-side validation and loading spinner on submit.

### 3. Prediction Result Card (`/result/<id>`)
- High-contrast visual decision card (`APPROVED` in emerald green or `REJECTED` in rose crimson).
- Precise approval confidence probability percentage and risk classification tier.
- Complete audit summary of all applicant parameters submitted.
- **Explainable AI (XAI)**: Identifies the top positive drivers supporting approval and top negative risk factors hindering approval.
- Prominent advisory disclaimer highlighting that the output is a predictive decision-support estimate.

### 4. Prediction History & Export (`/history`)
- Real-time search by Application ID, Applicant Name, Education, or Property Area.
- Filter by Approval or Rejection status.
- Direct CSV Export endpoint (`/export-history`) generating `loanwise_prediction_history.csv`.
- Individual record deletion and total history wipe modal.

### 5. Model Performance Page (`/performance`)
- Display of actual holdout test metrics: **Accuracy (86.18%)**, **Precision (84.00%)**, **Recall (98.82%)**, **F1-Score (90.81%)**, **ROC-AUC (85.26%)**.
- Interactive **Confusion Matrix Visualization** breaking down True Negatives (22), False Positives (16), False Negatives (1), and True Positives (84).
- Full **Classification Report** table with per-class and weighted averages.

### 6. Model Insights & Interpretability (`/insights`)
- Horizontal bar chart of **Logistic Regression Coefficients** (Log-odds weights).
- Complete feature coefficients inventory table.
- Dataset distribution graphs:
  - Credit History vs. Approval Rate (Good Credit: 79.6% vs Poor Credit: 8.0%).
  - Property Area Approval Distribution (Semiurban highest at 76.8%).
  - Education vs. Approval Rate.
- Explicit non-causality disclaimer explaining statistical association versus causal relationships.

---

## 7. Key Talking Points for Internship Review

1. **Why Logistic Regression?**
   - High interpretability (critical for regulated financial underwriting where "Right to Explanation" is mandated by compliance laws).
   - Calibrated probabilistic outputs via sigmoid function $P(Y=1|X) = \frac{1}{1 + e^{-z}}$.
   - Robust baseline resistant to overfitting on tabular banking datasets.

2. **How was Data Leakage Avoided?**
   - Imputation medians and scaling parameters ($\mu, \sigma$) were calculated **strictly on the training split** via `ColumnTransformer` and transformed onto test/inference inputs without snooping test distributions.

3. **Domain Insight:**
   - As reflected in the model weights, **Credit History** is the single most dominant predictor ($\beta \approx +1.70$), mirroring real-world commercial credit scoring where past repayment behavior is the strongest indicator of future default risk.


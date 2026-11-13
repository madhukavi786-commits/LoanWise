"""
LoanWise - Model Training & Evaluation Pipeline
Trains a Logistic Regression model within a ColumnTransformer pipeline,
computes comprehensive evaluation metrics, extracts feature importance,
and persists artifacts to the model/ directory.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

from preprocessing import (
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    create_model_pipeline
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, 'dataset', 'loan_data.csv')
MODEL_DIR = os.path.join(BASE_DIR, 'model')
MODEL_PATH = os.path.join(MODEL_DIR, 'loan_model.joblib')
METRICS_PATH = os.path.join(MODEL_DIR, 'metrics.json')


def load_dataset():
    """Loads and performs initial structural checks on the loan dataset."""
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at: {DATASET_PATH}")
    
    df = pd.read_csv(DATASET_PATH)
    print(f"[INFO] Loaded dataset with shape: {df.shape}")
    return df


def extract_dataset_overview(df):
    """Computes statistical overview and distributions for Model Insights."""
    total_records = int(len(df))
    approved_count = int((df['Loan_Status'] == 'Y').sum())
    rejected_count = int((df['Loan_Status'] == 'N').sum())
    approval_rate = round((approved_count / total_records) * 100, 2)

    # Property Area distribution
    property_counts = df['Property_Area'].value_counts().to_dict()
    property_approval = df.groupby('Property_Area')['Loan_Status'].apply(
        lambda s: round(float((s == 'Y').mean()) * 100, 2)
    ).to_dict()

    # Credit History distribution
    ch_clean = df['Credit_History'].dropna()
    credit_counts = {
        'Good Credit (1.0)': int((ch_clean == 1.0).sum()),
        'Poor Credit (0.0)': int((ch_clean == 0.0).sum()),
        'Missing': int(df['Credit_History'].isnull().sum())
    }
    credit_approval = df.groupby('Credit_History')['Loan_Status'].apply(
        lambda s: round(float((s == 'Y').mean()) * 100, 2)
    ).to_dict()
    # Format keys as string for JSON serialization
    credit_approval_str = {
        'Meets Guidelines (1.0)': credit_approval.get(1.0, 0.0),
        'Does Not Meet (0.0)': credit_approval.get(0.0, 0.0)
    }

    # Education distribution
    edu_counts = df['Education'].value_counts().to_dict()
    edu_approval = df.groupby('Education')['Loan_Status'].apply(
        lambda s: round(float((s == 'Y').mean()) * 100, 2)
    ).to_dict()

    return {
        'total_records': total_records,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'approval_rate': approval_rate,
        'property_counts': property_counts,
        'property_approval': property_approval,
        'credit_counts': credit_counts,
        'credit_approval': credit_approval_str,
        'education_counts': edu_counts,
        'education_approval': edu_approval,
        'missing_values': {col: int(cnt) for col, cnt in df.isnull().sum().items() if cnt > 0}
    }


def train_and_evaluate():
    """Executes the full training, validation, evaluation, and serialization routine."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    df = load_dataset()
    dataset_overview = extract_dataset_overview(df)

    # Feature Matrix & Target Vector
    X = df[FEATURE_COLUMNS].copy()
    y = df['Loan_Status'].map({'Y': 1, 'N': 0}).astype(int)

    # Stratified Train-Test Split (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )
    print(f"[INFO] Train samples: {len(X_train)} | Test samples: {len(X_test)}")

    # Instantiate and Fit Pipeline
    pipeline = create_model_pipeline()
    pipeline.fit(X_train, y_train)

    # Predictions & Probabilities
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    # Calculate Evaluation Metrics
    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob))

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]

    cm_formatted = {
        'matrix': cm.tolist(),
        'true_negatives': tn,
        'false_positives': fp,
        'false_negatives': fn,
        'true_positives': tp,
        'labels': ['Rejected (0)', 'Approved (1)']
    }

    # Classification Report
    cls_report = classification_report(
        y_test, y_pred,
        target_names=['Rejected (0)', 'Approved (1)'],
        output_dict=True
    )

    # Extract Model Coefficients & Feature Names
    preprocessor = pipeline.named_steps['preprocessor']
    classifier = pipeline.named_steps['classifier']
    feature_names = preprocessor.get_feature_names_out().tolist()
    coefficients = classifier.coef_[0].tolist()

    feature_importance = []
    for name, coef in zip(feature_names, coefficients):
        clean_name = name.replace('num__', '').replace('cat__', '').replace('_', ' ')
        feature_importance.append({
            'raw_name': name,
            'feature': clean_name,
            'coefficient': round(float(coef), 4),
            'abs_coefficient': round(float(abs(coef)), 4),
            'direction': 'Positive (Supports Approval)' if coef > 0 else 'Negative (Supports Rejection)'
        })

    # Sort descending by absolute coefficient
    feature_importance.sort(key=lambda x: x['abs_coefficient'], reverse=True)

    # Bundle all metrics & metadata
    metrics_bundle = {
        'training_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model_name': 'Logistic Regression (L-BFGS)',
        'pipeline_architecture': 'ColumnTransformer(Median Imputer + StandardScaler, Mode Imputer + OneHotEncoder) -> LogisticRegression',
        'train_samples': int(len(X_train)),
        'test_samples': int(len(X_test)),
        'accuracy': round(accuracy * 100, 2),
        'precision': round(precision * 100, 2),
        'recall': round(recall * 100, 2),
        'f1_score': round(f1 * 100, 2),
        'roc_auc': round(roc_auc * 100, 2),
        'confusion_matrix': cm_formatted,
        'classification_report': cls_report,
        'feature_importance': feature_importance,
        'dataset_overview': dataset_overview
    }

    # Persist artifacts
    joblib.dump(pipeline, MODEL_PATH)
    print(f"[SUCCESS] Trained model saved to: {MODEL_PATH}")

    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics_bundle, f, indent=4)
    print(f"[SUCCESS] Model metrics saved to: {METRICS_PATH}")

    # Output Summary Table
    print("\n" + "="*50)
    print("      LOANWISE MODEL EVALUATION SUMMARY")
    print("="*50)
    print(f"Accuracy:        {accuracy * 100:.2f}%")
    print(f"Precision:       {precision * 100:.2f}%")
    print(f"Recall:          {recall * 100:.2f}%")
    print(f"F1 Score:        {f1 * 100:.2f}%")
    print(f"ROC-AUC:         {roc_auc * 100:.2f}%")
    print(f"Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print("="*50 + "\n")

    return pipeline, metrics_bundle


if __name__ == '__main__':
    train_and_evaluate()


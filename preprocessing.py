"""
LoanWise - Data Preprocessing & Machine Learning Pipeline Module
Defines ColumnTransformer, Feature Pipelines, and Input Transformation.
"""

import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression

# Define numerical and categorical features
NUMERICAL_FEATURES = [
    'ApplicantIncome',
    'CoapplicantIncome',
    'LoanAmount',
    'Loan_Amount_Term'
]

CATEGORICAL_FEATURES = [
    'Gender',
    'Married',
    'Dependents',
    'Education',
    'Self_Employed',
    'Credit_History',
    'Property_Area'
]

FEATURE_COLUMNS = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


def create_preprocessor():
    """
    Creates a scikit-learn ColumnTransformer that applies:
    - Median imputation + StandardScaler for numerical features
    - Most frequent imputation + OneHotEncoder for categorical features
    """
    num_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    cat_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_pipeline, NUMERICAL_FEATURES),
            ('cat', cat_pipeline, CATEGORICAL_FEATURES)
        ],
        remainder='drop'
    )
    return preprocessor


def create_model_pipeline():
    """
    Builds the complete end-to-end Machine Learning Pipeline
    containing both preprocessing and Logistic Regression.
    """
    preprocessor = create_preprocessor()
    model = LogisticRegression(
        random_state=42,
        max_iter=1000,
        C=1.0,
        solver='lbfgs'
    )

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', model)
    ])
    return pipeline


def format_input_dataframe(data_dict):
    """
    Takes a raw dictionary of form inputs and formats it into a valid
    pandas DataFrame ready for pipeline.predict() or pipeline.predict_proba().
    """
    # Enforce correct types
    formatted_data = {
        'ApplicantIncome': [float(data_dict.get('applicant_income', 0.0))],
        'CoapplicantIncome': [float(data_dict.get('coapplicant_income', 0.0))],
        'LoanAmount': [float(data_dict.get('loan_amount', 0.0))],
        'Loan_Amount_Term': [float(data_dict.get('loan_amount_term', 360.0))],
        'Gender': [str(data_dict.get('gender', 'Male'))],
        'Married': [str(data_dict.get('married', 'No'))],
        'Dependents': [str(data_dict.get('dependents', '0'))],
        'Education': [str(data_dict.get('education', 'Graduate'))],
        'Self_Employed': [str(data_dict.get('self_employed', 'No'))],
        'Credit_History': [float(data_dict.get('credit_history', 1.0))],
        'Property_Area': [str(data_dict.get('property_area', 'Urban'))]
    }
    return pd.DataFrame(formatted_data)


def compute_feature_contributions(pipeline, df_input):
    """
    Calculates the relative contribution of each feature to the log-odds
    for an individual applicant, providing explainable AI (XAI) insights.
    """
    try:
        preprocessor = pipeline.named_steps['preprocessor']
        classifier = pipeline.named_steps['classifier']

        # Transform the single input sample
        transformed = preprocessor.transform(df_input)
        feature_names = preprocessor.get_feature_names_out()
        coefs = classifier.coef_[0]

        contributions = []
        for name, val, coef in zip(feature_names, transformed[0], coefs):
            impact = val * coef
            # Clean feature display name
            clean_name = name.replace('num__', '').replace('cat__', '').replace('_', ' ')
            contributions.append({
                'feature': clean_name,
                'raw_name': name,
                'weight': round(float(coef), 4),
                'transformed_value': round(float(val), 4),
                'impact': round(float(impact), 4)
            })

        # Sort by impact
        contributions.sort(key=lambda x: abs(x['impact']), reverse=True)
        top_positive = [c for c in contributions if c['impact'] > 0][:4]
        top_negative = [c for c in contributions if c['impact'] < 0][:4]

        return {
            'top_positive': top_positive,
            'top_negative': top_negative,
            'all_contributions': contributions[:10]
        }
    except Exception as e:
        return {'top_positive': [], 'top_negative': [], 'all_contributions': [], 'error': str(e)}


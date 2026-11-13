"""
LoanWise - Intelligent Underwriting Suggestions & Risk Profiler
Generates data-driven advisory recommendations, identifies financial strengths,
and details risk indicators based on applicant parameters and model outputs.
"""

def generate_underwriting_insights(applicant_data, prediction, probability):
    """
    Analyzes applicant financial and demographic parameters alongside model
    prediction probability to surface structured strengths, risk factors,
    and tailored loan improvement suggestions.
    """
    try:
        app_income = float(applicant_data.get('applicant_income', 0))
        coapp_income = float(applicant_data.get('coapplicant_income', 0))
        total_income = app_income + coapp_income
        loan_amount_k = float(applicant_data.get('loan_amount', 0))
        loan_amount_dollars = loan_amount_k * 1000.0
        term_months = float(applicant_data.get('loan_amount_term', 360))
        credit_history = float(applicant_data.get('credit_history', 1.0))
        education = str(applicant_data.get('education', 'Graduate'))
        self_employed = str(applicant_data.get('self_employed', 'No'))
        married = str(applicant_data.get('married', 'No'))
        dependents = str(applicant_data.get('dependents', '0'))
        property_area = str(applicant_data.get('property_area', 'Urban'))

        # Metrics for risk assessment
        annual_income = total_income * 12.0
        loan_to_income_ratio = (loan_amount_dollars / annual_income) if annual_income > 0 else 999.0

        strengths = []
        risk_indicators = []
        suggestions = []

        # 1. Credit History Assessment (Dominant Underwriting Pillar)
        if credit_history == 1.0:
            strengths.append({
                'title': 'Pristine Credit Track Record',
                'description': 'Applicant meets institutional credit bureau guidelines with no recorded derogatory marks or recent defaults.'
            })
        else:
            risk_indicators.append({
                'title': 'Adverse Credit History Flag',
                'description': 'Credit history does not meet standard guidelines. Past delinquencies or absence of verified repayment records represent the primary risk factor.'
            })
            suggestions.append({
                'category': 'Credit Profile',
                'action': 'Rebuild Credit Rating',
                'details': 'Prioritize settling outstanding revolving balances, dispute erroneous credit bureau entries, and maintain 6–12 months of on-time utility and credit card payments before re-applying.'
            })

        # 2. Income & Debt-to-Income / Loan-to-Income Analysis
        if total_income >= 6000:
            strengths.append({
                'title': 'Robust Household Income Stream',
                'description': f'Combined monthly earnings (${total_income:,.0f}) comfortably support monthly debt obligations.'
            })
        elif total_income < 3000:
            risk_indicators.append({
                'title': 'Constrained Monthly Cashflow',
                'description': f'Combined monthly income of ${total_income:,.0f} leaves minimal buffer for unforeseen debt service shocks.'
            })

        if loan_to_income_ratio > 3.0:
            risk_indicators.append({
                'title': 'Elevated Loan-to-Income Multiplier',
                'description': f'Requested loan (${loan_amount_dollars:,.0f}) exceeds {loan_to_income_ratio:.1f}x annual earnings, indicating potential debt burden.'
            })
            suggested_amount_k = round((annual_income * 2.5) / 1000.0)
            suggestions.append({
                'category': 'Loan Structuring',
                'action': 'Adjust Requested Principal',
                'details': f'Consider reducing requested loan from ${loan_amount_k:,.0f}k to approximately ${suggested_amount_k:,.0f}k to align closer with sustainable debt service ratios.'
            })
        elif loan_to_income_ratio <= 2.2 and total_income > 0:
            strengths.append({
                'title': 'Conservative Loan Leverage',
                'description': f'Requested loan is only {loan_to_income_ratio:.1f}x annual income, well within prudent institutional limits.'
            })

        # 3. Co-Applicant Impact
        if coapp_income > 0:
            strengths.append({
                'title': 'Dual-Income Risk Mitigation',
                'description': f'Co-applicant contributes ${coapp_income:,.0f}/mo ({round((coapp_income / total_income) * 100)}% of household cashflow), lowering individual default risk.'
            })
        else:
            if total_income < 4500 and prediction == 0:
                suggestions.append({
                    'category': 'Application Enhancement',
                    'action': 'Add a Co-Signer or Guarantor',
                    'details': 'Adding an earning spouse, parent, or business co-applicant will immediately increase the qualifying household income pool and improve debt coverage.'
                })

        # 4. Tenure & Repayment Optimization
        if term_months < 240 and prediction == 0:
            suggestions.append({
                'category': 'Tenure Optimization',
                'action': 'Extend Loan Repayment Term',
                'details': f'Current loan term ({int(term_months)} months) concentrates principal amortization. Extending to 360 months (30 years) lowers the monthly installment, improving affordability.'
            })

        # 5. Stability & Demographics
        if education == 'Graduate':
            strengths.append({
                'title': 'Professional Career Stability',
                'description': 'Applicant holds a graduate educational qualification, correlating statistically with career advancement and long-term earnings potential.'
            })
        if married == 'Yes':
            strengths.append({
                'title': 'Household Demographic Stability',
                'description': 'Married status is associated in historical lending portfolios with higher household asset accumulation.'
            })

        if self_employed == 'Yes':
            risk_indicators.append({
                'title': 'Self-Employment Income Volatility',
                'description': 'Self-employed income streams typically exhibit higher cyclical variance compared to salaried positions.'
            })
            suggestions.append({
                'category': 'Income Verification',
                'action': 'Provide Audited Financials',
                'details': 'Bolster self-employment documentation with two full years of verified tax returns, bank balance sheets, and steady contract commitments.'
            })

        if dependents in ['2', '3+']:
            risk_indicators.append({
                'title': 'Dependent Cost Factor',
                'description': f'Supporting {dependents} dependents increases monthly household nondiscretionary living expenditures.'
            })

        # 6. Property Area Underwriting Context
        if property_area == 'Semiurban':
            strengths.append({
                'title': 'Favorable Collateral Zoning',
                'description': 'Semiurban residential properties exhibit the highest portfolio recovery and liquidity rates in the benchmark dataset.'
            })
        elif property_area == 'Rural' and prediction == 0:
            suggestions.append({
                'category': 'Collateral Assurance',
                'action': 'Supplementary Collateral Valuation',
                'details': 'Rural real estate typically faces extended liquidation cycles. Securing a secondary certified appraisal or offering additional liquid collateral can satisfy underwriting requirements.'
            })

        # Default fallback suggestion if list is sparse
        if len(suggestions) == 0:
            suggestions.append({
                'category': 'Financial Discipline',
                'action': 'Maintain Credit & Liquidity Buffers',
                'details': 'Continue preserving 3–6 months of living expenses in liquid reserves while avoiding opening new credit lines prior to loan closing.'
            })

        return {
            'strengths': strengths[:4],
            'risk_indicators': risk_indicators[:4],
            'suggestions': suggestions[:4],
            'loan_to_income_ratio': round(loan_to_income_ratio, 2)
        }
    except Exception as e:
        return {
            'strengths': [],
            'risk_indicators': [],
            'suggestions': [{
                'category': 'General',
                'action': 'Maintain Good Credit Records',
                'details': 'Ensure all credit commitments are paid on time and maintain verifiable income documentation.'
            }],
            'loan_to_income_ratio': 0.0,
            'error': str(e)
        }


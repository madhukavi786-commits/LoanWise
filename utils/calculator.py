"""
LoanWise - Financial Mathematics & Loan Calculations
Implements standard Equated Monthly Installment (EMI) algorithms,
amortization breakdowns, and FOIR-based borrowing eligibility estimation.
"""

def calculate_emi(principal, annual_interest_rate, tenure_months):
    """
    Calculates monthly EMI, total interest, and total payable amount.
    
    Formula:
        E = P * r * (1 + r)^n / ((1 + r)^n - 1)
        where:
            P = Principal loan amount
            r = Monthly interest rate (annual_rate / 12 / 100)
            n = Total duration in months
    """
    try:
        p = float(principal)
        annual_rate = float(annual_interest_rate)
        n = int(tenure_months)

        if p <= 0 or annual_rate <= 0 or n <= 0:
            return {
                'emi': 0.0,
                'total_interest': 0.0,
                'total_repayment': 0.0,
                'principal': p,
                'principal_percentage': 0.0,
                'interest_percentage': 0.0,
                'error': 'Principal, interest rate, and tenure must all be positive numbers.'
            }

        # Monthly interest rate
        r = (annual_rate / 100.0) / 12.0

        # EMI calculation
        numerator = p * r * ((1.0 + r) ** n)
        denominator = ((1.0 + r) ** n) - 1.0

        if denominator == 0:
            emi = p / n
        else:
            emi = numerator / denominator

        total_repayment = emi * n
        total_interest = total_repayment - p

        principal_pct = round((p / total_repayment) * 100, 1) if total_repayment > 0 else 0.0
        interest_pct = round((total_interest / total_repayment) * 100, 1) if total_repayment > 0 else 0.0

        return {
            'emi': round(emi, 2),
            'total_interest': round(total_interest, 2),
            'total_repayment': round(total_repayment, 2),
            'principal': round(p, 2),
            'annual_rate': round(annual_rate, 2),
            'tenure_months': n,
            'tenure_years': round(n / 12.0, 1),
            'principal_percentage': principal_pct,
            'interest_percentage': interest_pct,
            'error': None
        }
    except Exception as e:
        return {
            'emi': 0.0,
            'total_interest': 0.0,
            'total_repayment': 0.0,
            'principal': 0.0,
            'principal_percentage': 0.0,
            'interest_percentage': 0.0,
            'error': str(e)
        }


def calculate_loan_eligibility(monthly_income, existing_emis=0.0, annual_interest_rate=9.5, tenure_months=360, foir=0.50):
    """
    Estimates maximum loan eligibility based on the standard banking
    FOIR (Fixed Obligation to Income Ratio) model.
    
    Default FOIR is 50% (0.50) of gross monthly income.
    """
    try:
        income = float(monthly_income)
        existing = float(existing_emis)
        annual_rate = float(annual_interest_rate)
        n = int(tenure_months)

        if income <= 0 or annual_rate <= 0 or n <= 0:
            return {
                'eligible_loan_amount': 0.0,
                'max_allowable_emi': 0.0,
                'available_monthly_capacity': 0.0,
                'foir_percentage': round(foir * 100, 1),
                'error': 'Income, interest rate, and tenure must be positive.'
            }

        max_allowable_emi = income * foir
        available_emi = max_allowable_emi - existing

        if available_emi <= 0:
            return {
                'eligible_loan_amount': 0.0,
                'max_allowable_emi': round(max_allowable_emi, 2),
                'available_monthly_capacity': 0.0,
                'foir_percentage': round(foir * 100, 1),
                'note': 'Existing obligations exceed the 50% debt-service capacity threshold.'
            }

        r = (annual_rate / 100.0) / 12.0
        # Inverted EMI formula: P = E * ((1+r)^n - 1) / (r * (1+r)^n)
        factor = ((1.0 + r) ** n) - 1.0
        denominator = r * ((1.0 + r) ** n)

        eligible_principal = available_emi * (factor / denominator)

        return {
            'eligible_loan_amount': round(eligible_principal, 2),
            'max_allowable_emi': round(max_allowable_emi, 2),
            'available_monthly_capacity': round(available_emi, 2),
            'monthly_income': round(income, 2),
            'existing_emis': round(existing, 2),
            'foir_percentage': round(foir * 100, 1),
            'tenure_months': n,
            'annual_rate': round(annual_rate, 2),
            'error': None
        }
    except Exception as e:
        return {
            'eligible_loan_amount': 0.0,
            'max_allowable_emi': 0.0,
            'available_monthly_capacity': 0.0,
            'foir_percentage': round(foir * 100, 1),
            'error': str(e)
        }


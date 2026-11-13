/**
 * LoanWise - Smart Customer Loan Approval Prediction System
 * Frontend Interactions & Chart.js Visualizations
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const appSidebar = document.getElementById('appSidebar');

    if (sidebarToggleBtn && appSidebar) {
        sidebarToggleBtn.addEventListener('click', () => {
            appSidebar.classList.toggle('show');
        });
    }

    // 2. Predict Form Submission State
    const predictForm = document.getElementById('loanPredictForm');
    const submitBtn = document.getElementById('predictSubmitBtn');

    if (predictForm && submitBtn) {
        predictForm.addEventListener('submit', (e) => {
            // Check form validity
            if (!predictForm.checkValidity()) {
                return;
            }
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Evaluating Application...
            `;
        });
    }

    // 3. Quick-fill Sample Profiles for Demo
    window.fillSampleProfile = (profileType) => {
        const form = document.getElementById('loanPredictForm');
        if (!form) return;

        if (profileType === 'prime') {
            document.getElementById('applicant_name').value = 'Jonathan Vance';
            document.getElementById('gender').value = 'Male';
            document.getElementById('married').value = 'Yes';
            document.getElementById('dependents').value = '1';
            document.getElementById('education').value = 'Graduate';
            document.getElementById('self_employed').value = 'No';
            document.getElementById('applicant_income').value = '6500';
            document.getElementById('coapplicant_income').value = '2200';
            document.getElementById('loan_amount').value = '150';
            document.getElementById('loan_amount_term').value = '360';
            document.getElementById('credit_history').value = '1.0';
            document.getElementById('property_area').value = 'Semiurban';
        } else if (profileType === 'high_risk') {
            document.getElementById('applicant_name').value = 'Arthur Pendelton';
            document.getElementById('gender').value = 'Male';
            document.getElementById('married').value = 'No';
            document.getElementById('dependents').value = '0';
            document.getElementById('education').value = 'Not Graduate';
            document.getElementById('self_employed').value = 'Yes';
            document.getElementById('applicant_income').value = '2400';
            document.getElementById('coapplicant_income').value = '0';
            document.getElementById('loan_amount').value = '210';
            document.getElementById('loan_amount_term').value = '360';
            document.getElementById('credit_history').value = '0.0';
            document.getElementById('property_area').value = 'Rural';
        } else if (profileType === 'moderate') {
            document.getElementById('applicant_name').value = 'Claire Redfield';
            document.getElementById('gender').value = 'Female';
            document.getElementById('married').value = 'No';
            document.getElementById('dependents').value = '1';
            document.getElementById('education').value = 'Graduate';
            document.getElementById('self_employed').value = 'No';
            document.getElementById('applicant_income').value = '4200';
            document.getElementById('coapplicant_income').value = '1400';
            document.getElementById('loan_amount').value = '180';
            document.getElementById('loan_amount_term').value = '180';
            document.getElementById('credit_history').value = '1.0';
            document.getElementById('property_area').value = 'Urban';
        }
    };
});


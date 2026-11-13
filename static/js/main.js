/**
 * LoanWise – Smart Customer Loan Approval Prediction System
 * Frontend Interactions, Client Validation & Dynamic Calculators
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Sidebar Toggle
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const appSidebar = document.getElementById('appSidebar');

    if (sidebarToggleBtn && appSidebar) {
        sidebarToggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            appSidebar.classList.toggle('show');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth < 992 && appSidebar.classList.contains('show')) {
                if (!appSidebar.contains(e.target) && e.target !== sidebarToggleBtn) {
                    appSidebar.classList.remove('show');
                }
            }
        });
    }

    // 2. Predict Form Submission State
    const predictForm = document.getElementById('loanPredictForm');
    const submitBtn = document.getElementById('predictSubmitBtn');

    if (predictForm && submitBtn) {
        predictForm.addEventListener('submit', (e) => {
            if (!predictForm.checkValidity()) {
                return;
            }
            submitBtn.disabled = true;
            submitBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                Evaluating Application with ML Engine...
            `;
        });
    }

    // 3. Quick-fill Sample Profiles for Demo Testing
    window.fillSampleProfile = (profileType) => {
        const form = document.getElementById('loanPredictForm');
        if (!form) return;

        if (profileType === 'prime') {
            const nameEl = document.getElementById('applicant_name');
            if (nameEl) nameEl.value = 'Eleanor Vance';
            document.getElementById('gender').value = 'Female';
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
            const nameEl = document.getElementById('applicant_name');
            if (nameEl) nameEl.value = 'Marcus Brody';
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
            const nameEl = document.getElementById('applicant_name');
            if (nameEl) nameEl.value = 'Devon Patel';
            document.getElementById('gender').value = 'Male';
            document.getElementById('married').value = 'Yes';
            document.getElementById('dependents').value = '2';
            document.getElementById('education').value = 'Graduate';
            document.getElementById('self_employed').value = 'No';
            document.getElementById('applicant_income').value = '5200';
            document.getElementById('coapplicant_income').value = '1800';
            document.getElementById('loan_amount').value = '175';
            document.getElementById('loan_amount_term').value = '240';
            document.getElementById('credit_history').value = '1.0';
            document.getElementById('property_area').value = 'Urban';
        }
    };

    // 4. Client-side Interactive EMI Calculator Engine
    window.runEmiCalculation = () => {
        const principalInput = document.getElementById('emiPrincipal');
        const rateInput = document.getElementById('emiRate');
        const tenureMonthsInput = document.getElementById('emiTenureMonths');

        if (!principalInput || !rateInput || !tenureMonthsInput) return;

        const p = parseFloat(principalInput.value) || 0;
        const rate = parseFloat(rateInput.value) || 0;
        const n = parseInt(tenureMonthsInput.value) || 0;

        if (p <= 0 || rate <= 0 || n <= 0) return;

        const r = (rate / 100.0) / 12.0;
        const factor = Math.pow(1 + r, n);
        const emi = (p * r * factor) / (factor - 1);
        const totalPayable = emi * n;
        const totalInterest = totalPayable - p;

        // Update DOM elements
        const emiResultEl = document.getElementById('resultEmiVal');
        const interestResultEl = document.getElementById('resultInterestVal');
        const totalResultEl = document.getElementById('resultTotalVal');

        if (emiResultEl) emiResultEl.textContent = '$' + emi.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        if (interestResultEl) interestResultEl.textContent = '$' + totalInterest.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        if (totalResultEl) totalResultEl.textContent = '$' + totalPayable.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});

        // Update or render Chart.js pie if exists
        if (window.emiDoughnutChart) {
            window.emiDoughnutChart.data.datasets[0].data = [Math.round(p), Math.round(totalInterest)];
            window.emiDoughnutChart.update();
        }
    };
});

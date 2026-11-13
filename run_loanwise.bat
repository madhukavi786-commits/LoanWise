@echo off
echo ===================================================
echo   LoanWise: Smart Customer Loan Approval System
echo ===================================================
echo.

IF EXIST "D:\anaconda\python.exe" (
    SET "PY_CMD=D:\anaconda\python.exe"
) ELSE (
    SET "PY_CMD=python"
)

echo [1/2] Verifying Machine Learning Model...
%PY_CMD% train_model.py
echo.
echo [2/2] Starting Flask Application Server...
echo Web server will run at: http://127.0.0.1:5000
echo.
%PY_CMD% app.py
pause


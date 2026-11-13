# LoanWise PowerShell Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  LoanWise: Smart Customer Loan Approval System" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

$pythonCmd = "python"
if (Test-Path "D:\anaconda\python.exe") {
    $pythonCmd = "D:\anaconda\python.exe"
}

Write-Host "[1/2] Verifying Model Artifacts..." -ForegroundColor Yellow
& $pythonCmd train_model.py

Write-Host "`n[2/2] Launching Flask Web Application..." -ForegroundColor Green
Write-Host "Open your browser at: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host ""
& $pythonCmd app.py


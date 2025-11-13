# PowerShell script to start the OCR server
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting OCR Text Extraction Server..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher" -ForegroundColor Red
    exit 1
}

# Check if model exists
if (Test-Path "Mymodel.pt") {
    Write-Host "Model file found: Mymodel.pt" -ForegroundColor Green
} else {
    Write-Host "WARNING: Mymodel.pt not found!" -ForegroundColor Yellow
    Write-Host "Some features may not work." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting server..." -ForegroundColor Cyan
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start the server
python app.py


# Script to start Frontend and Backend if they are not running

Write-Host "Checking if services are running..." -ForegroundColor Cyan

# Check if Frontend is running (typically on port 5173 for Vite)
$frontendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction SilentlyContinue
    $frontendRunning = $true
    Write-Host "Frontend is already running on port 5173" -ForegroundColor Green
} catch {
    Write-Host "Frontend is not running" -ForegroundColor Yellow
}

# Check if Backend is running (typically on port 8000)
$backendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -TimeoutSec 2 -ErrorAction SilentlyContinue
    $backendRunning = $true
    Write-Host "Backend is already running on port 8000" -ForegroundColor Green
} catch {
    Write-Host "Backend is not running" -ForegroundColor Yellow
}

# Start Frontend if not running
if (-not $frontendRunning) {
    Write-Host "Starting Frontend..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"
    Start-Sleep -Seconds 2
    Write-Host "Frontend started in new window" -ForegroundColor Green
} else {
    Write-Host "Frontend already running, skipping..." -ForegroundColor Green
}

# Start Backend if not running
if (-not $backendRunning) {
    Write-Host "Starting Backend..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
    Start-Sleep -Seconds 2
    Write-Host "Backend started in new window" -ForegroundColor Green
} else {
    Write-Host "Backend already running, skipping..." -ForegroundColor Green
}

Write-Host "`nDone! Services should be running now." -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan


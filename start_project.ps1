# PowerShell script to start KLIPPS project
Write-Host "🎯 Starting KLIPPS Project..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Yellow

# Start Backend Server
Write-Host "🚀 Starting Backend Server..." -ForegroundColor Cyan
$backendJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\Arqam Asghar\Desktop\imageprocessing\imageprocessing"
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Test backend connection
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Backend is running!" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Backend might still be starting..." -ForegroundColor Yellow
}

# Start Mobile App
Write-Host "📱 Starting Mobile App..." -ForegroundColor Cyan
$mobileJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\Arqam Asghar\Desktop\imageprocessing\klipps_app"
    flutter run
}

# Keep the script running
Write-Host "Both services are starting..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Red

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job $mobileJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $mobileJob -ErrorAction SilentlyContinue
} 
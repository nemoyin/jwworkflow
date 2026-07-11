# Start jwworkflow services in separate windows
Write-Host "Starting jwworkflow services..." -ForegroundColor Green

# Kill existing processes on our ports
Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}
Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2

# Start backend
$backendCmd = "cd D:\AI\opc\jwworkflow\backend; `$env:JWT_SECRET='test-secret'; `$env:LLM_API_KEY='sk-dc42126e667a4e899fa68fc3f70b00b7'; uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"
Start-Process powershell -WindowStyle Normal -ArgumentList "-NoExit", "-Command", $backendCmd
Write-Host "Backend started on :8080" -ForegroundColor Cyan

Start-Sleep -Seconds 3

# Start frontend
$frontendCmd = "cd D:\AI\opc\jwworkflow\frontend; npm run dev -- --host 0.0.0.0 --port 5173"
Start-Process powershell -WindowStyle Normal -ArgumentList "-NoExit", "-Command", $frontendCmd
Write-Host "Frontend started on :5173" -ForegroundColor Cyan

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  Backend:  http://localhost:8080" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "  Login:    admin@demo.com / demo123" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Yellow

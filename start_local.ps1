# 启动 jwworkflow 本地服务（分离 PowerShell 窗口）
Write-Host "正在启动 jwworkflow 服务..." -ForegroundColor Green

# 停止已有进程
Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}
Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2

# 启动后端
$backendCmd = "cd D:\AI\opc\jwworkflow\backend; `$env:JWT_SECRET='test-secret'; `$env:LLM_API_KEY='sk-dc42126e667a4e899fa68fc3f70b00b7'; uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"
Start-Process powershell -WindowStyle Normal -ArgumentList "-NoExit", "-Command", $backendCmd
Write-Host "后端已启动 [port 8080]" -ForegroundColor Cyan

Start-Sleep -Seconds 4

# 启动前端
$frontendCmd = "cd D:\AI\opc\jwworkflow\frontend; npm run dev -- --host 0.0.0.0 --port 5173"
Start-Process powershell -WindowStyle Normal -ArgumentList "-NoExit", "-Command", $frontendCmd
Write-Host "前端已启动 [port 5173]" -ForegroundColor Cyan

Write-Host ""
Write-Host "============================================" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8080" -ForegroundColor Green
Write-Host "  Login:    admin@demo.com / demo123" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Yellow

# run_web.ps1 — Backend web + token LiveKit; logs en logs\web.log
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
New-Item -ItemType Directory -Force -Path "$Root\logs" | Out-Null
$log = "$Root\logs\web.log"
Remove-Item $log -ErrorAction SilentlyContinue
Add-Content -Path $log -Value "=== inicio child web pid=$PID fecha=$([DateTime]::Now) ===" -Encoding utf8
Write-Host "Web en http://localhost:7860 ..." -ForegroundColor Cyan
& "$Root\.venv\Scripts\python.exe" -m uvicorn backend.api.main:app --port 7860 2>&1 | ForEach-Object { $_; Add-Content -Path $log -Value $_ -Encoding utf8 }
Write-Host "Web detenida (revisa logs\web.log)." -ForegroundColor Yellow
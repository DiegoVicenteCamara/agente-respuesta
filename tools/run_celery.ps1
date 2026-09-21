# run_celery.ps1 — Worker de subagentes; logs en logs\celery.log
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
New-Item -ItemType Directory -Force -Path "$Root\logs" | Out-Null
$log = "$Root\logs\celery.log"
Remove-Item $log -ErrorAction SilentlyContinue
Add-Content -Path $log -Value "=== inicio child celery pid=$PID fecha=$([DateTime]::Now) ===" -Encoding utf8
Write-Host "Celery worker (subagentes LangGraph)..." -ForegroundColor Cyan
& "$Root\.venv\Scripts\celery.exe" -A backend.orchestrator.tasks.celery_app worker -P solo -l info 2>&1 | ForEach-Object { $_; Add-Content -Path $log -Value $_ -Encoding utf8 }
Write-Host "Worker detenido (revisa logs\celery.log)." -ForegroundColor Yellow
# status.ps1 — Estado de los servicios del prototipo
$l = Get-NetTCPConnection -LocalPort 7860 -State Listen -ErrorAction SilentlyContinue
if ($l) { Write-Host 'PUERTO 7860: EN ESCUCHA' -ForegroundColor Green } else { Write-Host 'PUERTO 7860: LIBRE' -ForegroundColor Yellow }
Get-CimInstance Win32_Process |
  Where-Object { ($_.Name -match 'python|celery') -and ($_.CommandLine -match 'uvicorn|celery') } |
  Select-Object ProcessId, Name | Format-Table -AutoSize
# detener servicios del prototipo (worker + web)
if ($args -contains '-kill') {
    Get-CimInstance Win32_Process |
      Where-Object { ($_.Name -match 'python|celery') -and ($_.CommandLine -match 'uvicorn|celery') } |
      ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host 'Servicios detenidos' -ForegroundColor Cyan
}
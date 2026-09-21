# start_dev.ps1 — Arranca el prototipo localmente en Windows
# Requisito: Docker Desktop instalado y en marcha (dependencia: Redis).
# Uso:          powershell -ExecutionPolicy Bypass -File tools\start_dev.ps1
# Con voz:      ... -Voice   (necesita créditos OpenAI y el CLI de LiveKit)
param(
    [switch]$Voice
)
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

# 1) Localizar docker.exe (Docker Desktop se instala por usuario en AppData)
$Docker = $null
foreach ($cand in @(
        "docker",
        "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe",
        "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    )) {
    $cmd = Get-Command $cand -ErrorAction SilentlyContinue
    if ($cmd) { $Docker = $cmd.Source; break }
    if (Test-Path $cand) { $Docker = $cand; break }
}
if (-not $Docker) {
    throw "No se encontro docker.exe. Instala Docker Desktop y reinicia la sesion."
}
$env:PATH = "$(Split-Path $Docker);$env:PATH"
Write-Host "docker: $Docker" -ForegroundColor DarkGray

# 2) Docker en marcha
& $Docker info 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker Desktop no esta en marcha. Abrelo y espera a que indique 'Engine running'." -ForegroundColor Yellow
    Read-Host "Pulsa Enter cuando Docker este listo"
    & $Docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Docker sigue sin responder." }
}

# 3) Contenedor Redis (idempotente)
& $Docker inspect agente-redis 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Lanzando contenedor Redis en localhost:6379..." -ForegroundColor Cyan
    & $Docker run -d --name agente-redis -p 6379:6379 --restart unless-stopped redis:7-alpine 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Fallo al crear el contenedor Redis." }
}
& $Docker start agente-redis 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Fallo al arrancar el contenedor Redis." }

# 4) Esperar a que Redis responda PONG
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    $ping = & $Docker exec agente-redis redis-cli ping 2>$null
    if ($ping -eq "PONG") { $ready = $true; break }
    Start-Sleep -Milliseconds 500
}
if (-not $ready) { throw "Redis no respondio a 'ping'. Revisa el contenedor." }
Write-Host "Redis listo en localhost:6379" -ForegroundColor Green

# 5) Worker Celery (oculto, logs en logs\)
New-Item -ItemType Directory -Force -Path "$Root\logs" | Out-Null
Remove-Item "$Root\logs\celery.*.log","$Root\logs\web.*.log" -ErrorAction SilentlyContinue
Write-Host "Arrancando worker Celery (oculto)..." -ForegroundColor Cyan
$celProc = Start-Process -FilePath "$Root\.venv\Scripts\celery.exe" `
    -ArgumentList @('-A','backend.orchestrator.tasks.celery_app','worker','-P','solo','-l','info') `
    -WorkingDirectory $Root -WindowStyle Hidden `
    -RedirectStandardOutput "$Root\logs\celery.out.log" -RedirectStandardError "$Root\logs\celery.err.log" -PassThru

# 6) Backend web + token (oculto, logs en logs\)
Write-Host "Arrancando web http://localhost:7860 (oculta)..." -ForegroundColor Cyan
$webProc = Start-Process -FilePath "$Root\.venv\Scripts\python.exe" `
    -ArgumentList @('-m','uvicorn','backend.api.main:app','--port','7860') `
    -WorkingDirectory $Root -WindowStyle Hidden `
    -RedirectStandardOutput "$Root\logs\web.out.log" -RedirectStandardError "$Root\logs\web.err.log" -PassThru

# 7) Agente de voz (opcional, -Voice)
if ($Voice) {
    Write-Host "Arrancando agente de voz (requiere credito OpenAI y CLI LiveKit)..." -ForegroundColor Cyan
    Start-Process -FilePath "lk" -ArgumentList @('agent','dev') -WorkingDirectory $Root -WindowStyle Hidden `
        -RedirectStandardOutput "$Root\logs\agent.out.log" -RedirectStandardError "$Root\logs\agent.err.log"
}

# 8) Verificar arranque
$webOk = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-WebRequest -Uri 'http://localhost:7860' -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $webOk = $true; break }
    } catch { Start-Sleep -Seconds 1 }
}
if ($webOk) { Write-Host "Web OK http://localhost:7860" -ForegroundColor Green }
else { Write-Host "AVISO: la web no respondio. Revisa logs\web.err.log" -ForegroundColor Yellow }

$celeryOk = $false
for ($i = 0; $i -lt 20; $i++) {
    & "$Root\.venv\Scripts\celery.exe" -A backend.orchestrator.tasks.celery_app inspect ping --timeout 4 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $celeryOk = $true; break }
    Start-Sleep -Seconds 2
}
if ($celeryOk) { Write-Host "Celery worker OK (pid $($celProc.Id))" -ForegroundColor Green }
else { Write-Host "AVISO: worker Celery no responde. Revisa logs\celery.err.log" -ForegroundColor Yellow }

Write-Host ""
Write-Host "Listo: abre http://localhost:7860 en el navegador y pulsa Llamar." -ForegroundColor Green
Write-Host "Logs en logs\; detener: cierra los procesos o cierra Docker Desktop." -ForegroundColor DarkGray
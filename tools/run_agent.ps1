# run_agent.ps1 — Agente de voz (requiere créditos OpenAI y CLI de LiveKit: lk cloud auth)
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
Write-Host "Agente de voz (LiveKit dev)..." -ForegroundColor Cyan
& lk agent dev
Write-Host "Agente detenido." -ForegroundColor Yellow
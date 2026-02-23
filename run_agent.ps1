$ErrorActionPreference = "Stop"

if (-Not (Test-Path ".venv")) {
    Write-Host "Création de l'environnement virtuel..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Activation de l'environnement..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

Write-Host "Lancement de l'agent V4.1..." -ForegroundColor Green
python agent_local_v4_1.py

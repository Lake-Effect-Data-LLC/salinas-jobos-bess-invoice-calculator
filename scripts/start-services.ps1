$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Test-Path ".env.docker")) {
    Write-Host "Creating .env.docker from .env.docker.example..."
    Copy-Item ".env.docker.example" ".env.docker"
}

try {
    docker info | Out-Null
}
catch {
    throw "Docker Desktop is not running or Docker is unavailable. Start Docker Desktop, wait for it to finish starting, then rerun this task."
}

Write-Host "Starting local Postgres and MinIO with Docker Compose..."
docker compose --env-file .env.docker up -d

Write-Host ""
Write-Host "Services started."
Write-Host "Postgres: localhost:5433"
Write-Host "MinIO API: http://localhost:9001"
Write-Host "MinIO Console: http://localhost:9002"

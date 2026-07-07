$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Setting up BESS Invoice Calculator development environment..."

if (-not (Test-Path ".venv")) {
    $pythonLauncher = $null
    foreach ($candidate in @("3.13", "3.12", "3.11", "3.10")) {
        try {
            py -$candidate --version | Out-Null
            $pythonLauncher = "py -$candidate"
            break
        }
        catch {
            continue
        }
    }

    if ($null -eq $pythonLauncher) {
        try {
            python --version | Out-Null
            $pythonLauncher = "python"
        }
        catch {
            throw "Could not find Python. Install Python 3.13, 3.12, 3.11, or 3.10, then rerun this setup."
        }
    }

    Write-Host "Creating .venv with $pythonLauncher..."
    Invoke-Expression "$pythonLauncher -m venv .venv"
}
else {
    Write-Host ".venv already exists; reusing it."
}

Write-Host "Installing Python dependencies..."
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

if (-not (Test-Path ".env.docker")) {
    Write-Host "Creating .env.docker from .env.docker.example..."
    Copy-Item ".env.docker.example" ".env.docker"
}
else {
    Write-Host ".env.docker already exists; leaving it unchanged."
    $envText = Get-Content ".env.docker" -Raw
    if ($envText -match "DATABASE_URL=postgresql://") {
        Write-Host "Updating .env.docker DATABASE_URL to use the Psycopg 3 SQLAlchemy driver..."
        $envText = $envText -replace "DATABASE_URL=postgresql://", "DATABASE_URL=postgresql+psycopg://"
        Set-Content ".env.docker" $envText
    }
}

Write-Host ""
Write-Host "Setup complete."
Write-Host "Next: start Docker Desktop, then run scripts\start-services.cmd or the VS Code task 'BESS: 2 Start Local Services'."

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (Test-Path ".env.docker") {
    $databaseUrlLine = Get-Content ".env.docker" | Where-Object { $_ -match "^DATABASE_URL=" } | Select-Object -First 1
    if ($databaseUrlLine) {
        $env:DATABASE_URL = $databaseUrlLine -replace "^DATABASE_URL=", ""
    }
}

if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "postgresql+psycopg://bess_app:bluedesk@localhost:5433/bess_invoice"
}

if ($env:DATABASE_URL -match "^postgresql://") {
    $env:DATABASE_URL = $env:DATABASE_URL -replace "^postgresql://", "postgresql+psycopg://"
}

if (Test-Path ".\.venv\Scripts\python.exe") {
    $python = ".\.venv\Scripts\python.exe"
}
else {
    $python = "python"
}

Write-Host "Waiting for local Postgres on localhost:5433..."
& $python -c "import socket,time,sys; deadline=time.time()+60; last=None
while time.time()<deadline:
    try:
        s=socket.create_connection(('localhost',5433),timeout=2); s.close(); sys.exit(0)
    except Exception as e:
        last=e; time.sleep(2)
print(f'Postgres did not become reachable on localhost:5433 within 60 seconds: {last}', file=sys.stderr)
sys.exit(1)"

Write-Host "Importing CSV inputs into the local database..."
& $python "tools/import_csv_to_db.py"

Write-Host "Verifying DB-backed calculations against CSV-backed calculations..."
& $python "tools/verify_db_roundtrip.py"

Write-Host ""
Write-Host "Database seed and verification complete."

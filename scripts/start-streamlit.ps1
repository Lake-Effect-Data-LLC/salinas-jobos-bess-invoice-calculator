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

if (Test-Path ".\.venv\Scripts\streamlit.exe") {
    $streamlit = ".\.venv\Scripts\streamlit.exe"
    & $streamlit run "app/streamlit_app.py"
}
elseif (Test-Path ".\.venv\Scripts\python.exe") {
    & ".\.venv\Scripts\python.exe" -m streamlit run "app/streamlit_app.py"
}
else {
    streamlit run "app/streamlit_app.py"
}

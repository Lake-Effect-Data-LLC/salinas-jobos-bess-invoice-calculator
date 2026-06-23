# Database-Backed Streamlit Runtime

## Overview

The Streamlit app runtime is database-first. Users select a facility and dataset/scenario, edit database-backed input tables, run calculations, and download results from the database-backed workflow.

CSV files remain important, but they are no longer a live Streamlit runtime data source.

## Feature Behavior

Runtime app behavior:

- Select facility: Salinas or Jobos.
- Select dataset/scenario from the database.
- Create new datasets/scenarios.
- Edit input tables backed by Postgres.
- Run calculations from database-backed inputs.
- Download calculation outputs/report from the run result.

Removed runtime compatibility behavior:

- The `CSV / local files` vs `Database` data-source toggle.
- Drag-and-drop CSV input upload UI in the main Streamlit runtime.
- CSV validation/run path inside `streamlit_app.py`.

## Technical Details

Primary runtime files:

- `app/streamlit_app.py`
- `app/components/db_tables.py`
- `app/db/readers.py`
- `app/services/table_editor.py`

CSV support remains outside the runtime app:

- `tools/import_csv_to_db.py`
- `tools/verify_db_roundtrip.py`
- existing CSV data files under `data/`

## Rationale

The product direction is for Postgres to be the system of record. CSV should be import/export/audit tooling, not the steady-state input workflow in the app UI.

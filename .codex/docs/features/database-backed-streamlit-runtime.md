# Database-Backed Streamlit Runtime

## Overview

The Streamlit app runtime is database-first. Users select a facility and dataset/scenario, edit database-backed input tables, run calculations, and download results from the database-backed workflow.

CSV files remain important, but they are no longer a live Streamlit runtime data source.

## Feature Behavior

Runtime app behavior:

- Select facility: Salinas or Jobos.
- Select dataset/scenario from the database.
- Use a compact sidebar for facility and dataset/scenario selection.
- Create new datasets/scenarios.
- Edit input tables backed by Postgres.
- Add row-level notes directly in non-contract input tables when recording context for manual edits.
- Run calculations from database-backed inputs.
- Download calculation outputs/report from the run result.

Removed runtime compatibility behavior:

- The `CSV / local files` vs `Database` data-source toggle.
- Drag-and-drop CSV input upload UI in the main Streamlit runtime.
- CSV validation/run path inside `streamlit_app.py`.
- Form-level `Edit reason` and `Source` inputs for yearly inputs, monthly inputs, monthly performance guarantee rows, and performance tests.

Contract values:

- Contract values are currently displayed read-only.
- When contract values become editable, they should retain stricter provenance fields such as required edit reason/source because they represent contract/reference data.

## Technical Details

Primary runtime files:

- `app/streamlit_app.py`
- `app/components/db_tables.py`
- `app/db/readers.py`
- `app/services/table_editor.py`

Audit behavior:

- Non-contract input saves do not require form-level audit metadata.
- `row_edit_history` can still store nullable `edit_reason` and `source` values for these tables.
- Row-level `notes` remain part of the input records and are included in inserted/updated row data.

CSV support remains outside the runtime app:

- `tools/import_csv_to_db.py`
- `tools/verify_db_roundtrip.py`
- existing CSV data files under `data/`

## Rationale

The product direction is for Postgres to be the system of record. CSV should be import/export/audit tooling, not the steady-state input workflow in the app UI.

# Database-Backed Streamlit Runtime

## Overview

The Streamlit app runtime is database-first. Users select a facility and dataset/scenario, edit database-backed input tables, run calculations, and download results from the database-backed workflow.

CSV files remain important, but they are no longer a live Streamlit runtime data source.

## Feature Behavior

Runtime app behavior:

- Select facility: Salinas or Jobos.
- Select dataset/scenario from the database.
- Use a compact expanded sidebar for facility and dataset/scenario selection.
- Use a full-width main content container so dashboard/table space responds when the sidebar is collapsed.
- Render the banner as a full-width element within the main content area.
- Create new datasets/scenarios.
- Edit input tables backed by Postgres.
- Show concise contract-aware tooltips on input table column headers.
- Show collapsed `Column Guide` expanders beneath editable input tables for nearby data-entry reference.
- Add row-level notes directly in non-contract input tables when recording context for manual edits.
- Run calculations from database-backed inputs.
- Persist successful calculation runs to `monthly_snapshot`.
- Show a run-history dashboard above the input tables.
- Refresh the Latest Run dashboard after successful calculation runs while keeping the generated output visible.
- Download calculation outputs/report from the run result.

Run-history behavior:

- Calculation run summaries are represented with `monthly_snapshot` rows.
- Run snapshots are children of `dataset_config`; they record that a specific dataset/scenario was calculated at a specific time.
- Run snapshots are not separate datasets.
- Each successful calculation creates a new `monthly_snapshot` row.
- After a successful run is saved, the app reruns so Latest Run reloads from the database.
- Each snapshot represents the most recent calculated month from that calculation.
- The dashboard groups runs by `snapshot_month` and shows only the latest successful run for each month.
- Latest Run shows the most recent month prominently.
- Previous Runs shows the prior 12 months in a scrollable card list with `MP`, `MFP`, `CPP`, `MCC`, `FAA`, and `PRA`; CSV/report downloads sit under the month label for each previous run.
- Dashboard downloads use CSV/report text stored in `snapshot_data`; MinIO upload/download is intentionally not wired yet.
- CSV artifact metadata can still be represented with `file_object` rows when MinIO is added later.

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
- `app/components/column_tooltips.py`
- `app/components/run_dashboard.py`
- `app/db/readers.py`
- `app/db/run_history.py`
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

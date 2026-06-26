# Database-Backed Streamlit Runtime

## Overview

The Streamlit app runtime is database-first. Users select a facility and dataset/scenario, edit database-backed input tables, run calculations, and download results from the database-backed workflow.

CSV files remain important, but they are no longer a live Streamlit runtime data source.

## Feature Behavior

Runtime app behavior:

- Select facility: Salinas or Jobos.
- Select dataset/scenario from the database.
- Cache settings and SQLAlchemy engine creation with Streamlit resource caching so reruns reuse the same database engine/pool.
- Run a lightweight database connection check on every render so connection errors still surface promptly.
- Show a dynamic page title based on the selected facility and scenario.
- Preserve the selected facility and scenario in URL query params so browser reload keeps the same selection when valid.
- Use a compact expanded sidebar for facility and dataset/scenario selection.
- Use a full-width main content container so dashboard/table space responds when the sidebar is collapsed.
- Stack horizontal metric/chart/control rows on narrower screens to reduce squished layouts.
- Render the banner as a full-width element within the main content area.
- Create new datasets/scenarios.
- Edit input tables backed by Postgres.
- Use one input grid in normal mode so users can add new rows at the bottom of the existing table. Existing-row edits/deletes are still rejected at save time unless Override Mode is on.
- Use a sidebar `Override Mode` toggle to unlock existing-row edits/deletes; the main input-table area shows the warning and mandatory override editor when the toggle is active.
- In Override Mode, each table's save action is grouped in a native bordered container with a warning, override edit reason text area, and Save button.
- After a successful input-table save that inserts, updates, or deletes rows, the app generates one `audit_event_id` for the save action and writes it to every `row_edit_history` row created by that save.
- After a successful input-table save that inserts, updates, or deletes rows, the app exports the complete current scenario state to MinIO under `scenario_state/{project_id}/{dataset_name}/{audit_event_id}.csv` and `.json`. The artifacts include the audit event ID, changed table name, inserted/updated/deleted counts, override edit reason when provided, and sections for all five input tables.
- When the scenario-state MinIO upload succeeds, the matching `row_edit_history` rows are updated with the artifact bucket, CSV key, and JSON key so DBeaver can point directly to the related snapshot files.
- Show concise contract-aware tooltips on input table column headers.
- Show collapsed `Column Guide` expanders above editable input tables with a reminder that headers also support hover tooltips.
- Add row-level notes directly in non-contract input tables when recording context for manual edits.
- Run calculations from database-backed inputs.
- Persist successful calculation runs to `monthly_snapshot`.
- Show a two-column run dashboard above the input tables, with Latest Run on the left and Summary Comparison plus Previous Runs on the right.
- Refresh the Latest Run dashboard after successful calculation runs while keeping the generated output visible.
- Show a native `Analytics & Trends` section expanded by default after successful calculation output.
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
- Previous Runs is collapsed by default in the right side of the top run dashboard and shows the prior 12 months in a scrollable card list with `MP`, `MFP`, `CPP`, `MCC`, `FAA`, and `PRA`; CSV/report downloads sit under the month label for each previous run.
- After a successful run, a run audit CSV is uploaded to MinIO at `run_history/{project_id}/{dataset_name}/{YYYY-MM}/{snapshot_name}.csv` and a `file_object` row is created and linked to the snapshot via `source_file_object_id`. The CSV starts with monthly results and then includes sections for all five input tables used for the run.
- After a successful run, a companion JSON calculation package is also uploaded to MinIO at `run_history/{project_id}/{dataset_name}/{YYYY-MM}/{snapshot_name}.package.json`; it includes the latest-month summary, monthly results CSV text, report text, and all five input tables used for the run.
- CSV downloads in the run dashboard use a presigned MinIO URL (`st.link_button`) when a `file_object` is linked; older runs without a MinIO artifact fall back to `st.download_button` using text in `snapshot_data`.
- Report downloads always use `snapshot_data`; the report is not uploaded to MinIO.
- MinIO upload failures are non-fatal — the run and database snapshot succeed regardless.

Analytics behavior:

- Analytics uses the same grouped monthly run snapshots as Run History.
- Summary Comparison sits in the right side of the top run dashboard and lets the user select `MP`, `MFP`, `MCC`, `FAA %`, or `PRA %`.
- Summary Comparison shows a two-bar Altair chart comparing the latest run to the average of previous runs only, with readable horizontal labels, value labels, and a short delta sentence.
- Financial Trend charts `MP` and `MFP` over recent months.
- Generation Trend charts available operational output metrics from the summary snapshot: `MCC`, `FAA %`, and `PRA %`.
- Charts render through `st.altair_chart` with explicit axis labels.

Removed runtime compatibility behavior:

- The `CSV / local files` vs `Database` data-source toggle.
- Drag-and-drop CSV input upload UI in the main Streamlit runtime.
- CSV validation/run path inside `streamlit_app.py`.
- Form-level `Edit reason` and `Source` inputs for yearly inputs, monthly inputs, monthly performance guarantee rows, and performance tests.

Contract values:

- Contract values are displayed read-only in normal mode.
- Contract values can only be deleted in Override Mode; inserting and editing contract-value rows remains blocked.
- Contract-value deletes require Override Mode, edit reason, and audit logging because they represent contract/reference data.

## Technical Details

Primary runtime files:

- `app/streamlit_app.py`
- `app/components/db_tables.py`
- `app/components/column_tooltips.py`
- `app/components/analytics.py`
- `app/components/run_dashboard.py`
- `app/db/readers.py`
- `app/db/run_history.py`
- `app/services/table_editor.py`

Audit behavior:

- One input-table save action maps to one `audit_event_id`; multiple row inserts/updates/deletes from that save share the same ID.
- Non-contract input saves do not require form-level audit metadata.
- `row_edit_history` can still store nullable `edit_reason` and `source` values for these tables.
- Row-level `notes` remain part of the input records and are included in inserted/updated row data.
- Existing-row updates/deletes require Override Mode and an edit reason. Audit `source` remains nullable until an explicit editor/source field or authenticated user identity is wired in.
- Deletes are hard deletes from the input table after a `row_edit_history` row is written in the same transaction.
- `row_edit_history.created_at` supplies the audit timestamp. `edited_by` remains nullable until authenticated app users are wired into the runtime.
- `row_edit_history.artifact_bucket`, `artifact_csv_key`, and `artifact_json_key` are nullable because DB saves are allowed to succeed even if MinIO upload fails.

CSV support remains outside the runtime app:

- `tools/import_csv_to_db.py`
- `tools/verify_db_roundtrip.py`
- existing CSV data files under `data/`

## Rationale

The product direction is for Postgres to be the system of record. CSV should be import/export/audit tooling, not the steady-state input workflow in the app UI.

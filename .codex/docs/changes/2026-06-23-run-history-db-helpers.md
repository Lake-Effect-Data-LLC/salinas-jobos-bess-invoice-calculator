# User Request And Plan

> “Inspect the existing monthly_snapshot and file_object schema and implement database reader/writer helpers for calculation run history. Use monthly_snapshot for run summaries and file_object for CSV artifact metadata. Do not add new tables unless the current schema cannot support the workflow.”

## Plan

The existing schema can support this first slice without new tables:

- `monthly_snapshot` can store a calculation-run summary in `snapshot_data`.
- `monthly_snapshot.snapshot_month` can identify the most recent result month represented by the run.
- `monthly_snapshot.snapshot_name` can be a unique run label, such as `calculation_run_2026_...`.
- `monthly_snapshot.source_file_object_id` can point to the CSV artifact metadata.
- `file_object` can store the MinIO bucket/key/checksum/size metadata for the CSV artifact.

This change will:

- Add database writer helpers for CSV artifact metadata and calculation run snapshots.
- Add database reader helpers for latest/recent calculation runs.
- Export the helpers from `app.db`.
- Add focused tests using an in-memory SQLite schema that mirrors the needed columns.
- Avoid schema changes unless implementation proves the current tables cannot support the workflow.

## Verification Plan

- Run Python compilation for the new module.
- Run the unit test suite.

---

# Feature Changes

- Added database helpers for calculation run-history metadata without changing the schema.
- Calculation run summaries are stored in `monthly_snapshot.snapshot_data` as JSON.
- CSV artifact metadata is stored in `file_object` with `object_type = 'csv_export'`.
- Recent/latest run readers join `monthly_snapshot` to `file_object` so the future dashboard can show both summary metrics and download metadata.
- A transaction-level writer can create the optional CSV artifact record and calculation snapshot together.

---

# Files Changed

- `app/db/run_history.py`
  - Added snapshot-name generation.
  - Added CSV export file-object writer.
  - Added calculation snapshot writer.
  - Added combined calculation-run writer.
  - Added latest/recent run readers and file-object lookup.
  - Handles PostgreSQL `jsonb` inserts while staying testable against SQLite.

- `app/db/__init__.py`
  - Exported the new run-history helpers through the DB package.

- `tests/test_run_history.py`
  - Added SQLite-backed tests for snapshot-name generation, run recording, CSV artifact metadata, latest run lookup, and recent-run ordering.

- `docs/action_items.md`
  - Marked run-history display and MinIO CSV export as `Partial` because the DB metadata foundation now exists, while UI and storage integration remain separate tasks.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the planned run-history storage behavior and the new `app/db/run_history.py` module.

---

# Summary And Concerns

The existing schema supports this slice. No new tables were added. The app now has a clear DB boundary for future run-history/dashboard work:

- `monthly_snapshot` stores calculation run summaries.
- `file_object` stores CSV artifact metadata.
- `source_file_object_id` links a run snapshot to the CSV object metadata.

Verification completed:

- `python -m py_compile app/db/run_history.py app/db/__init__.py`
- `python -m unittest discover -s tests` ran 46 tests successfully.

Concerns:

- This does not upload files to MinIO yet.
- This does not render the dashboard yet.
- The unique constraint on `monthly_snapshot` means callers should use unique `snapshot_name` values for repeated runs in the same month. The helper generates timestamped names by default.

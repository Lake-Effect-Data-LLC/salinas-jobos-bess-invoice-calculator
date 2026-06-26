# Request

Two pretty major things. Can we make the new state of the scenario dataset dump into the MinIO, and when we dump into minio on a calculation, can we include all of the monthly and other inputs as the screenshot?

---

## Plan

1. Keep the current database-backed save and run flows intact.
2. Add MinIO JSON artifacts rather than changing database schema:
   - Scenario state snapshot after successful input-table saves.
   - Full calculation package after successful calculation runs.
3. Reuse `load_inputs_snapshot()` so all five input tables are captured consistently:
   - `contract_values`
   - `yearly_inputs`
   - `monthly_inputs`
   - `monthly_performance_guarantee`
   - `performance_tests`
4. Keep the existing calculation CSV upload and dashboard CSV download behavior unchanged.
5. Treat MinIO upload failures as non-fatal, matching the existing calculation CSV upload behavior.
6. Add tests for the artifact payload builders and storage key helpers.

---

## Feature Changes

- Successful input-table saves now export the complete current scenario state to MinIO as JSON.
- Successful calculation runs still upload the monthly results CSV for dashboard downloads.
- Successful calculation runs now also upload a companion JSON package to MinIO with:
  - latest-month summary
  - monthly results CSV text
  - invoice support report text
  - all five input tables used for the run
- Storage upload failures remain non-fatal so database saves and calculation runs can still complete.

---

## Files Changed

- `app/artifacts.py`
  - Added reusable builders for scenario-state and calculation-package JSON artifacts.
  - Added `artifact_to_json_bytes()` for stable JSON serialization.
- `app/storage.py`
  - Added `scenario_state/` key support.
  - Kept `run_history/` key support and allowed package keys such as `.package.json`.
  - Moved `boto3`/`botocore` imports inside `get_storage_client()` so non-storage tests can import key helpers without requiring storage dependencies at import time.
- `app/streamlit_app.py`
  - After successful table saves, uploads scenario-state JSON to MinIO.
  - After successful calculation runs, uploads the existing CSV and a companion JSON calculation package to MinIO.
- `app/components/db_tables.py`
  - Added an optional `on_saved` callback that runs after successful row-changing saves.
  - Skips the callback when Save is clicked but no rows changed.
- `tests/test_artifacts.py`
  - Added tests for artifact payloads and MinIO key structure.
- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented scenario-state exports and calculation-package exports.
- `docs/action_items.md`
  - Marked the MinIO export item as done for the current implemented scope.
- `.codex/docs/changes/2026-06-25-minio-scenario-and-run-input-artifacts.md`
  - Added this implementation record.

---

## Summary And Concerns

The app now stores richer MinIO artifacts without changing the database schema or breaking existing dashboard CSV downloads.

Object layout:

```text
scenario_state/{project_id}/{dataset_name}/scenario_state_{timestamp}.json
run_history/{project_id}/{dataset_name}/{YYYY-MM}/{snapshot_name}.csv
run_history/{project_id}/{dataset_name}/{YYYY-MM}/{snapshot_name}.package.json
```

The scenario-state JSON represents the current dataset/scenario after an input-table save. The calculation package JSON represents the exact inputs and outputs for a successful run.

Verification:
- `python -m unittest tests.test_artifacts tests.test_results_snapshot tests.test_run_history tests.test_table_editor_normalization` passed.
- `python -m py_compile app/artifacts.py app/storage.py app/streamlit_app.py app/components/db_tables.py app/components/results.py app/db/readers.py` passed.
- `python -m unittest discover -s tests` passed: 69 tests.

Concerns:
- The companion JSON package is uploaded to MinIO but is not currently exposed as a download button in the UI.
- The package artifact does not get its own `file_object` row because the current schema links one artifact from `monthly_snapshot.source_file_object_id`, and that link is still reserved for the dashboard CSV download.
- MinIO failures are intentionally swallowed, matching the existing run CSV upload behavior. That keeps user workflows moving but means failed artifact uploads need logs/observability later.

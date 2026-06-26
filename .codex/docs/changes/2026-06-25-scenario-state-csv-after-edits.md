# Request

I thought I made it clear that I want all of that saved after a delete or edit!

---

## Plan

1. Keep the existing callback that runs after successful input-table saves with inserted, updated, or deleted rows.
2. Extend the scenario-state MinIO export so edit/delete saves upload a CSV artifact as well as JSON.
3. Put all five input tables in that scenario-state CSV as labeled sections.
4. Keep the calculation-run CSV behavior unchanged.
5. Add tests for the input-table CSV builder and scenario-state CSV storage key.

---

## Feature Changes

- After any successful input-table save that inserts, updates, or deletes rows, MinIO now receives a CSV scenario-state artifact.
- The scenario-state CSV contains all five input tables as labeled sections.
- The existing scenario-state JSON artifact remains in place.
- Calculation-run CSV behavior remains unchanged.

---

## Files Changed

- `app/components/results.py`
  - Added `build_inputs_csv_text()` for exporting only the five input-table sections.
  - Reused the same input-section writer for calculation-run CSVs and scenario-state CSVs.
- `app/storage.py`
  - Extended `build_scenario_state_key()` so scenario-state artifacts can use `.csv` or `.json`.
- `app/streamlit_app.py`
  - Updated `_upload_scenario_state()` to upload both CSV and JSON after row-changing table saves.
- `tests/test_results_snapshot.py`
  - Added coverage that the input-only CSV includes all five input-table sections.
- `tests/test_artifacts.py`
  - Added coverage for the scenario-state `.csv` MinIO key.
- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented that insert/update/delete saves export both CSV and JSON scenario-state artifacts.
- `.codex/docs/changes/2026-06-25-scenario-state-csv-after-edits.md`
  - Added this implementation record.

---

## Summary And Concerns

The post-save MinIO export now matches the intended audit behavior. If a user edits or deletes input-table rows and saves successfully, the app uploads the full current scenario state as:

```text
scenario_state/{project_id}/{dataset_name}/scenario_state_{timestamp}.csv
scenario_state/{project_id}/{dataset_name}/scenario_state_{timestamp}.json
```

The CSV contains:

```text
SECTION,contract_values
...

SECTION,yearly_inputs
...

SECTION,monthly_inputs
...

SECTION,monthly_performance_guarantee
...

SECTION,performance_tests
...
```

Verification:
- `python -m unittest tests.test_results_snapshot tests.test_artifacts` passed.
- `python -m py_compile app/components/results.py app/streamlit_app.py app/storage.py` passed.
- `python -m unittest discover -s tests` passed: 71 tests.

Concern:
- These artifacts are saved to MinIO but are not yet surfaced in the Streamlit UI as a scenario-state download/history list.

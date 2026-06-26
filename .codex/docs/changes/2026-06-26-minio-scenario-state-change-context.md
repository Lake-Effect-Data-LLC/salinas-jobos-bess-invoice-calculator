# Request

Alright!

Context from the preceding discussion: add the edit/delete reason and change summary into the MinIO scenario-state artifacts after successful input-table saves.

---

## Plan

1. Pass table save context from `app/components/db_tables.py` into the `on_saved` callback:
   - changed table name
   - inserted/updated/deleted counts
   - override edit reason
2. Add that context to the scenario-state JSON artifact.
3. Add a `change_summary` section at the top of the scenario-state CSV artifact.
4. Keep current five-input-table export behavior unchanged.
5. Add focused tests for the JSON and CSV artifact builders.

---

## Feature Changes

- Scenario-state MinIO artifacts now include save context for row-changing input-table saves.
- The context includes:
  - changed table name
  - inserted count
  - updated count
  - deleted count
  - override edit reason
- Scenario-state CSV artifacts now start with a `change_summary` section before the five input-table sections.
- Scenario-state JSON artifacts now include a `change_context` object next to `inputs`.

---

## Files Changed

- `app/components/db_tables.py`
  - Passes table name, change counts, and edit reason into the `on_saved` callback after successful saves.
- `app/streamlit_app.py`
  - Threads change context into `_upload_scenario_state()`.
  - Writes the context into both scenario-state CSV and JSON uploads.
- `app/artifacts.py`
  - Adds optional `change_context` support to scenario-state JSON artifacts.
- `app/components/results.py`
  - Adds optional `change_summary` CSV section support to `build_inputs_csv_text()`.
- `tests/test_artifacts.py`
  - Covers scenario-state JSON `change_context`.
- `tests/test_results_snapshot.py`
  - Covers scenario-state CSV `change_summary`.
- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documents the MinIO scenario-state change context behavior.
- `.codex/docs/changes/2026-06-26-minio-scenario-state-change-context.md`
  - Added this implementation record.

---

## Summary And Concerns

MinIO scenario-state artifacts now explain both the new state and why/how it changed. After a successful edit/delete/insert save, the CSV starts like:

```text
SECTION,change_summary
field,value
table_name,monthly_inputs
inserted,0
updated,0
deleted,1
edit_reason,Removed duplicate month
```

The JSON includes:

```json
"change_context": {
  "table_name": "monthly_inputs",
  "change_result": {
    "inserted": 0,
    "updated": 0,
    "deleted": 1
  },
  "edit_reason": "Removed duplicate month"
}
```

Verification:
- `python -m unittest tests.test_artifacts tests.test_results_snapshot` passed.
- `python -m py_compile app/artifacts.py app/components/results.py app/components/db_tables.py app/streamlit_app.py` passed.
- `python -m unittest discover -s tests` passed: 73 tests.

Concern:
- The MinIO scenario-state artifacts are still not surfaced in the UI as a history/download list.

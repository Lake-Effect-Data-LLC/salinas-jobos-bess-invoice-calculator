# Snapshot: Include Input Tables

---

## Original Request

> "in order for a snapshot of a run to be effective, there should be all of the monthly inputs that gave that run, right? Can you do allat?"

---

## Plan

### Overview

Currently `snapshot_data` only stores calculation outputs (`latest_month_summary`, `csv_text`, `report_text`). A snapshot without its inputs cannot be reproduced or audited independently. This change adds all 5 input tables to `snapshot_data` at the moment a run is recorded.

### Approach

Add `load_inputs_snapshot(engine, project_id, dataset_name)` to `readers.py` — a separate DB read that loads all 5 input tables as plain JSON-serializable dicts (not domain objects). Call it in `render_database_flow` after the calculation and pass the result into `build_run_snapshot_data`.

This keeps the calculation flow unchanged and makes the snapshot self-contained.

### Snapshot structure after change

```json
{
  "latest_month_summary": {...},
  "csv_text": "...",
  "report_text": "...",
  "inputs": {
    "contract_values": [...],
    "yearly_inputs": [...],
    "monthly_inputs": [...],
    "monthly_performance_guarantee": [...],
    "performance_tests": [...]
  }
}
```

### Files to change

| File | Change |
|---|---|
| `app/db/readers.py` | Add `load_inputs_snapshot`, `_df_to_records`, `_json_safe_value` |
| `app/components/results.py` | `build_run_snapshot_data` accepts optional `inputs` kwarg |
| `app/streamlit_app.py` | Import and call `load_inputs_snapshot`, pass result into `build_run_snapshot_data` |

---

## Feature Changes

### Self-contained run snapshots

Every new calculation run now records the complete state of all 5 input tables alongside the outputs in `snapshot_data`. Historical snapshots (before this change) are unaffected — `inputs` will simply be absent from their `snapshot_data`.

---

## File Changes

### `app/db/readers.py`
- Added `load_inputs_snapshot(engine, project_id, dataset_name)` — loads all 5 input tables as lists of JSON-safe dicts in a single connection
- Added `_df_to_records(df)` — converts a DataFrame to a list of dicts with JSON-safe values
- Added `_json_safe_value(value)` — converts dates, datetimes, Decimals, and NaN to JSON-serializable types

### `app/components/results.py`
- `build_run_snapshot_data` accepts optional `inputs=None` kwarg
- When provided, `inputs` is included in the returned snapshot dict under the `"inputs"` key

### `app/streamlit_app.py`
- Imported `load_inputs_snapshot` from `app.db.readers`
- After calculation, calls `load_inputs_snapshot(engine, project_id, dataset_name)` and passes result to `build_run_snapshot_data`

---

## Summary

Run snapshots are now self-contained: anyone reading a `monthly_snapshot` row from the database has everything needed to understand and reproduce the result. Old snapshots are unaffected. The implementation is a clean, separate DB read with no changes to the calculation path.

### Concerns / Known Gaps

- **Double DB read** — inputs are read once for calculation (domain objects) and once for the snapshot (raw dicts). For this tool size that is negligible, but a future optimisation could return raw records from the calculation readers directly.
- **`inputs` absent on old snapshots** — any UI feature that reads `snapshot_data["inputs"]` must handle the key being missing.

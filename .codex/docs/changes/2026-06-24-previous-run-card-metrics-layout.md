# User Request And Plan

> “Update the Previous Runs dashboard cards so they show the same metrics as Latest Run. Move the CSV and Report download buttons under the month/date on the left side of each previous-run card. Use the remaining horizontal space for MP, MFP, CPP, MCC, FAA, and PRA. Keep MP and MFP visually prominent, keep CPP/MCC/FAA/PRA smaller but visible, and fix formatting so currency values do not awkwardly truncate. Do not change run-history persistence or MinIO behavior. Update tests/docs only if needed.”

## Plan

This is a dashboard layout-only change:

- Keep run-history persistence unchanged.
- Keep MinIO untouched.
- Move Previous Runs download buttons below each month label.
- Show `MP`, `MFP`, `CPP`, `MCC`, `FAA`, and `PRA` on each previous-run card.
- Use custom markdown metric blocks for previous runs instead of narrow `st.metric` blocks so currency values can wrap/fit better.

## Verification Plan

- Run Python compilation for `app/components/run_dashboard.py`.

---

# Feature Changes

- Previous Runs cards now show the same dashboard metric set as Latest Run: `MP`, `MFP`, `CPP`, `MCC`, `FAA`, and `PRA`.
- CSV and Report download buttons now sit under the month label for each previous run.
- Previous Runs metrics use custom text blocks instead of narrow `st.metric` widgets to reduce awkward currency truncation.
- No persistence, schema, or MinIO behavior changed.

---

# Files Changed

- `app/components/run_dashboard.py`
  - Updated `_render_previous_runs()` layout.
  - Added `_render_metric_block()` for previous-run metric display.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the Previous Runs metric set and download placement.

---

# Summary And Concerns

The previous-run cards now use their left side for month-specific actions and the remaining width for comparable metrics. This makes prior months easier to scan against the Latest Run without changing the underlying run-history behavior.

Verification completed:

- `python -m py_compile app/components/run_dashboard.py`

Concern:

- Visual browser verification was not run in this pass. The layout should be checked in Streamlit because exact wrapping depends on viewport width and Streamlit's generated column styles.

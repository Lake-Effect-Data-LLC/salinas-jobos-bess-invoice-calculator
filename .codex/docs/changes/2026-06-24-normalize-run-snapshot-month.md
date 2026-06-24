# User Request And Plan

> Screenshot shows `Run Calculation` failing when saving `monthly_snapshot`: invalid input syntax for type date, with `snapshot_month` like `2027-12`.

## Plan

The calculation output can use month strings in `YYYY-MM` format, but `monthly_snapshot.snapshot_month` is a Postgres `date`. The run-history writer should normalize any snapshot month value to the first day of the month before insert.

This change will:

- Normalize `snapshot_month` values in `app/db/run_history.py`.
- Preserve dashboard month labels and grouping behavior.
- Add regression coverage for `YYYY-MM` snapshot months.

## Verification Plan

- Run Python compilation for the touched modules.
- Run the unit test suite.

---

# Feature Changes

- Run snapshot persistence now accepts `YYYY-MM` month values from calculation output.
- Snapshot months are normalized to first-of-month dates before writing to `monthly_snapshot.snapshot_month`.
- This prevents Postgres date insert failures like `invalid input syntax for type date: "2027-12"`.

---

# Files Changed

- `app/db/run_history.py`
  - Added `_month_start_iso()`.
  - Changed snapshot inserts to normalize `snapshot_month` through `_month_start_iso()`.

- `tests/test_run_history.py`
  - Added regression coverage for saving a run with `snapshot_month="2027-12"`.

- `.codex/docs/features/dataset-scenarios.md`
  - Documented that `monthly_snapshot.snapshot_month` is stored as the first day of the month.

---

# Summary And Concerns

The dashboard save failure was caused by inserting a month string into a Postgres `date` column. The persistence layer now converts month values to valid first-of-month ISO dates, so calculations with `timestamp_month` values like `2027-12` can be saved.

Verification completed:

- `python -m py_compile app/db/run_history.py tests/test_run_history.py`
- `python -m unittest discover -s tests` ran 50 tests successfully.

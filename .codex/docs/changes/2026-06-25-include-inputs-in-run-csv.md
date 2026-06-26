# Request

Is this clear? This jawn here, I want him to contain the values of the five input files. Type shi

---

## Plan

1. Treat the referenced MinIO object as the run CSV artifact: `calculation_run_....csv`.
2. Change the run CSV artifact content so it includes:
   - monthly calculation results
   - contract values
   - yearly inputs
   - monthly inputs
   - monthly performance guarantee
   - performance tests
3. Keep the existing separate JSON package artifact in place.
4. Preserve the current dashboard download path, so the CSV button downloads the richer CSV automatically.
5. Add tests proving the CSV text includes all five input sections.

---

## Feature Changes

- The MinIO run CSV artifact now contains a full run audit export rather than only monthly results.
- The CSV starts with the monthly calculation results and then includes five labeled input sections:
  - `contract_values`
  - `yearly_inputs`
  - `monthly_inputs`
  - `monthly_performance_guarantee`
  - `performance_tests`
- Existing dashboard CSV download behavior stays the same, but the downloaded CSV is now richer.

---

## Files Changed

- `app/components/results.py`
  - Added `build_run_csv_text()` to build a sectioned CSV export.
  - Updated `build_run_snapshot_data()` so `snapshot_data["csv_text"]` contains monthly results plus input-table sections when inputs are available.
- `tests/test_results_snapshot.py`
  - Added assertions that the run CSV includes all five input-table sections.
  - Added coverage for the no-input fallback case.
- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the run audit CSV behavior.
- `docs/action_items.md`
  - Updated the MinIO action item notes to reflect the richer CSV export.
- `.codex/docs/changes/2026-06-25-include-inputs-in-run-csv.md`
  - Added this implementation record.

---

## Summary And Concerns

The specific MinIO `.csv` object shown in the screenshot now receives the five input tables as part of the CSV body. This is done by replacing the old output-only CSV text with a sectioned audit CSV:

```text
SECTION,monthly_results
...

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
- `python -m unittest tests.test_results_snapshot tests.test_artifacts tests.test_run_history` passed.
- `python -m py_compile app/components/results.py app/streamlit_app.py app/artifacts.py app/storage.py` passed.
- `python -m unittest discover -s tests` passed: 70 tests.

Concern:
- This keeps the artifact as a single CSV, so Excel will show one worksheet with labeled sections rather than separate tabs. A true multi-tab workbook would require an `.xlsx` artifact.

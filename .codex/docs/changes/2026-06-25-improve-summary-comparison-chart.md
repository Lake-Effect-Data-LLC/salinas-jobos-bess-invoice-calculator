# Request

Best improvement: keep the two bars, make them wider, use horizontal labels, add value labels above each bar, and add a small delta line like:
Latest is $184,320 higher than previous average (+8.7%)
That would make it immediately useful instead of just technically correct.

---

## Plan

The Summary Comparison chart already uses the correct data source and chart type. The improvement is presentation:

1. Keep the existing two-bar latest-vs-average comparison.
2. Make the category labels horizontal and readable.
3. Make the bars visually stronger for a two-category chart.
4. Add labels directly on the bars.
5. Add a concise delta sentence comparing latest to the previous-runs average.
6. Run focused analytics tests and compile checks.

---

## Feature Changes

- Improved the Summary Comparison graph so it reads as an immediate decision aid instead of a bare technical chart.
- The selected metric now shows a plain-language delta sentence comparing Latest Run against the previous-runs average.
- The bar chart keeps the two-bar structure but uses wider bars, horizontal x-axis labels, shortened visual labels, and direct value labels.

---

## Files Changed

- `app/components/analytics.py`
  - Added metric display metadata for currency, number, and percent values.
  - Added `build_summary_delta_text()` for the latest-vs-average summary sentence.
  - Updated the Summary Comparison Altair chart to use readable labels and value labels.

- `tests/test_analytics.py`
  - Added focused tests for currency and percent delta text.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the improved Summary Comparison behavior.

---

## Summary And Concerns

The Summary Comparison graph now communicates both the numeric comparison and the practical takeaway. It remains based on the existing run-history data and does not change calculations, database schema, MinIO behavior, or persistence.

Verification:

- `.\.venv\Scripts\python.exe -m py_compile app\components\analytics.py`
- `.\.venv\Scripts\python.exe -m unittest tests.test_analytics`

Browser verification was attempted against the running local app, but the browser-control runtime failed before navigation with a workspace URI setup error. The app itself returned HTTP 200 at `http://localhost:8503`.

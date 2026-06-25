# User Request And Plan

> "I want to adjust the layout of the Run History and Dashboard section at the top of the app. Please refactor the UI using Streamlit's st.columns and st.expander to achieve the following layout:
> 1. Two-Column Layout: Split the top section into a left and right column (e.g., using col1, col2 = st.columns([1, 1]) or similar proportions).
> 2. Left Column: Place the 'Latest Run' information and its primary metrics here.
> 3. Right Column (Statistics): Place the summary statistics and the summary graph in the right column.
> 4. Right Column (Previous Runs): Place the 'Previous Runs' list in the right column as well (you can place it either above or below the statistics, whichever flows better visually).
> 5. Collapsible Previous Runs: Wrap the entire 'Previous Runs' list inside an st.expander("Previous Runs") so that it is collapsible and keeps the UI clean by default.
> Please show me the updated Streamlit layout code for this section."

## Plan

Refactor the top calculation review section into one coordinated two-column layout.

- Keep one database fetch for grouped monthly run history.
- Left column: render Latest Run metrics and downloads.
- Right column: render Summary Comparison first, then a collapsed Previous Runs expander.
- Reuse the existing Altair summary comparison logic by adding a from-runs renderer.
- Remove the separate top-level Summary Comparison call from `streamlit_app.py`.
- Preserve calculation, database schema, persistence, and snapshot behavior.
- Verify touched Python files compile and analytics tests pass.

---

# Feature Changes

- The top run dashboard now uses a two-column layout.
- Latest Run renders in the left column.
- Summary Comparison renders in the right column.
- Previous Runs now renders inside a collapsed `Previous Runs` expander in the right column.
- Summary Comparison and Previous Runs share the same run-history fetch as Latest Run.

---

# Files Changed

- `app/components/run_dashboard.py`
  - Imports `render_summary_comparison_from_runs`.
  - Uses `st.columns([1, 1])` for the top Run History layout.
  - Places Latest Run in the left column.
  - Places Summary Comparison and collapsed Previous Runs in the right column.
  - Removes the standalone `Previous Runs` markdown heading because the expander now provides the label.

- `app/components/analytics.py`
  - Added `render_summary_comparison_from_runs(...)` so already-loaded run history can feed the chart.
  - Kept the existing `render_summary_comparison(...)` wrapper for direct use if needed.

- `app/streamlit_app.py`
  - Removed the separate top-level `render_summary_comparison(...)` call so the dashboard owns the top layout.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the two-column dashboard and collapsed Previous Runs behavior.

---

# Summary And Concerns

This refactor consolidates the top calculation review area into one layout: Latest Run on the left, Summary Comparison and Previous Runs on the right. It keeps the same run-history data source and avoids duplicate run-history queries for the top chart.

Verification completed:

- `python -m py_compile app/components/analytics.py app/components/run_dashboard.py app/streamlit_app.py`
- `python -m unittest tests.test_analytics`

Concern:

- The top-level split is currently `[1, 1]` as requested. If laptop screens feel cramped, tune this ratio after visual review.

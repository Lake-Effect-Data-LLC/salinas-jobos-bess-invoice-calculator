# User Request And Plan

> add a top-of-page Summary Comparison expander above Run History.
> It will:
> Load the same run-history snapshot data already used by the dashboard.
> Let the user pick a metric from a dropdown: MP, MFP, MCC, FAA %, or PRA %.
> Show a two-bar chart:Latest Run
> Previous Runs Average
>
> Exclude the latest run from the average.
> Use Altair via st.altair_chart so the chart has proper axis labels.
> Update the existing bottom Analytics & Trends charts to use Altair too, so their axes are labeled clearly.
> No database/schema changes. No calculation changes.

## Plan

Implement the requested analytics upgrade using existing run-history snapshots.

- Add a top `Summary Comparison` expander above Run History.
- Fetch grouped latest-run-per-month data using `list_latest_calculation_runs_by_month(...)`.
- Let the user select `MP`, `MFP`, `MCC`, `FAA %`, or `PRA %`.
- Compare the latest run against the average of previous runs only.
- Render the comparison with Altair bar charts and explicit axis labels.
- Replace bottom `st.line_chart` usage with Altair line charts and explicit axis labels.
- Add tests for comparison-frame aggregation.
- Avoid database schema, persistence, MinIO, and calculation changes.

---

# Feature Changes

- Added a top-of-page `Summary Comparison` expander above Run History.
- Added a metric dropdown for `MP`, `MFP`, `MCC`, `FAA %`, and `PRA %`.
- Added an Altair two-bar chart comparing `Latest Run` to `Previous Runs Average`.
- The previous-run average excludes the latest run.
- Replaced bottom `Analytics & Trends` `st.line_chart` calls with Altair line charts that have explicit axis labels.

---

# Files Changed

- `app/components/analytics.py`
  - Added `render_summary_comparison(...)`.
  - Added `build_summary_comparison_frame(...)`.
  - Added Altair chart helpers for comparison bars and trend lines.
  - Kept analytics data sourced from `list_latest_calculation_runs_by_month(...)`.

- `app/streamlit_app.py`
  - Renders `Summary Comparison` above Run History.

- `tests/test_analytics.py`
  - Added coverage for excluding the latest run from the previous-run average.
  - Added coverage for percent normalization in summary comparisons.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented Summary Comparison and Altair-labeled chart behavior.

---

# Summary And Concerns

The analytics area now uses Altair through Streamlit for labeled axes and better chart control. The top Summary Comparison expander gives a quick latest-vs-history view without changing how runs are calculated or stored. The bottom trend charts keep the same data but now render with explicit `Billing Month` and value-axis labels.

Verification completed:

- `python -m py_compile app/components/analytics.py app/streamlit_app.py`
- `python -m unittest tests.test_analytics`

Concern:

- The Summary Comparison average uses the available previous grouped monthly snapshots, up to the existing 12-run analytics limit. If the product wants a longer historical average later, increase `ANALYTICS_RUN_LIMIT`.

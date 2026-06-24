# User Request And Plan

> "I want to implement a 'Concise graphing summary' at the bottom of our Streamlit page, appearing below the input tables and edit history after a calculation is run.
> Based on our design constraints, here is what this analytics section should look like:
> 1. Placement: Add an expander or a dedicated container at the bottom of the page titled 'Analytics & Trends'.
> 2. Data Source: Pull the historical output data from our database (the same data we use for the Run History). We want to visualize trends over time ('how it's changed').
> 3. What to Graph: Please create two simple, side-by-side Streamlit charts (st.line_chart or st.bar_chart):
> - Financial Trend: A chart tracking 'Amount Due' over time. Specifically, plot the summary numbers for MP (Monthly Payment) and MFP (Monthly Fixed Payment) across the recent months.
> - Generation Trend: A chart tracking facility 'Generation' metrics over time across the recent months.
> 4. Keep it Native: Use Streamlit's native charting functions to keep the implementation lightweight for now. We don't need a massive Plotly/Altair setup yet, just a quick visual summary of the outputs.
> Please outline the SQL query or data aggregation needed to fetch this time-series data, and show me the Streamlit code to render these two charts at the bottom of the page."

## Plan

Implement a lightweight native Streamlit analytics section using existing run-history snapshots.

- Add a new `app/components/analytics.py` component.
- Use `list_latest_calculation_runs_by_month(...)` so the charts use the same grouped latest-run-per-month data as Run History.
- Build a chronological financial dataframe from `snapshot_data.latest_month_summary.MP` and `MFP`.
- Build a chronological operational/generation dataframe from available summary metrics: `MCC`, `FAA`, and `PRA`.
- Render a collapsed `Analytics & Trends` expander with two side-by-side native `st.line_chart` charts.
- Show the analytics section below calculation output after a successful calculation rerun.
- Add focused tests for the dataframe aggregation.
- Avoid database schema, persistence, MinIO, and calculation changes.

---

# Feature Changes

- Added a collapsed `Analytics & Trends` expander below the successful calculation output.
- Added two native Streamlit line charts:
  - Financial Trend: `MP` and `MFP` over recent months.
  - Generation Trend: `MCC`, `FAA %`, and `PRA %` over recent months.
- Analytics pulls from `monthly_snapshot` through the existing grouped latest-run-per-month run-history helper.

---

# Files Changed

- `app/components/analytics.py`
  - Added `render_analytics_summary(...)`.
  - Added `build_analytics_trend_frames(...)` to convert run snapshots into chart dataframes.
  - Uses `list_latest_calculation_runs_by_month(...)` with a 12-month limit.

- `app/streamlit_app.py`
  - Renders the analytics summary below saved calculation output after a successful run.

- `tests/test_analytics.py`
  - Added tests for chronological trend frame construction, financial metrics, operational metrics, and empty rows.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the new analytics behavior.

---

# Summary And Concerns

The analytics section stays lightweight and native to Streamlit. It uses the same run-history aggregation as the dashboard:

```sql
WITH ranked_runs AS (
    SELECT
        snapshot.id AS snapshot_id,
        snapshot.snapshot_month,
        snapshot.snapshot_name,
        snapshot.snapshot_data,
        snapshot.created_at,
        row_number() OVER (
            PARTITION BY snapshot.snapshot_month
            ORDER BY snapshot.created_at DESC, snapshot.id DESC
        ) AS run_rank
    FROM monthly_snapshot snapshot
    WHERE snapshot.dataset_config_id = :dataset_config_id
      AND snapshot.snapshot_name LIKE 'calculation_run_%'
)
SELECT snapshot_month, snapshot_data
FROM ranked_runs
WHERE run_rank = 1
ORDER BY snapshot_month DESC
LIMIT :limit;
```

The component reverses those newest-first rows into chronological order before rendering line charts.

Verification completed:

- `python -m py_compile app/components/analytics.py app/streamlit_app.py`
- `python -m unittest tests.test_analytics`

Concern:

- The existing run snapshot does not contain a field literally named `Generation`. The current implementation uses the available operational output metrics `MCC`, `FAA %`, and `PRA %`. If the product needs actual MWh generation/discharge trend lines, the snapshot payload should be expanded to include that source field explicitly.

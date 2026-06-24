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

Pending implementation.

---

# Files Changed

Pending implementation.

---

# Summary And Concerns

Pending implementation.

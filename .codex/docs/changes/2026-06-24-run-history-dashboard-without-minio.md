# User Request And Plan

> “Implement the Streamlit run-history dashboard without MinIO. Use the existing monthly_snapshot run-history structure and scope all dashboard data to the selected project + dataset_config.
> Requirements:
> Persist every successful calculation run to monthly_snapshot.
> Each run should represent the most recent calculated month from that calculation.
> Store enough snapshot_data to support dashboard display and downloads without MinIO:latest month summary row
> full monthly results CSV text
> invoice support report text
>
> Dashboard UI should appear near the top of the page, above input tables.
> If there are no runs, show No runs yet.
> Frontend history should group runs by snapshot_month.
> For each month, show only the latest successful run.
> Latest Run section should show the most recent month prominently.
> Previous Runs section should show the prior 12 months.
> Headline amount due is MP.
> MFP basis/generation metrics should show MFP, CPP, MCC, FAA, and PRA.
> Add Easy Download controls for both CSV and text report using stored snapshot_data, not MinIO.
> Do not implement MinIO upload/download yet.
> Keep all changes consistent with existing DB/service/component boundaries.
> Add tests for grouping latest run per month and snapshot payload creation.
> Update persistent docs and action tracker.”

## Plan

Implement the dashboard as a no-MinIO database-backed slice:

- Add a pure snapshot payload builder that stores latest month summary, full CSV text, and report text.
- Add a grouped run-history reader that returns the latest successful run per `snapshot_month`.
- Add a Streamlit dashboard component that shows latest run, previous 12 monthly runs, and CSV/report download buttons from `snapshot_data`.
- Persist successful Streamlit calculations into `monthly_snapshot` after calculation succeeds.
- Keep `file_object`/MinIO out of this task.
- Add focused tests for payload creation and grouping by month.
- Update persistent feature docs and action tracker.

## Verification Plan

- Run Python compilation for changed app modules.
- Run the unit test suite.

---

# Feature Changes

- Successful Streamlit calculations now persist a `monthly_snapshot` run record.
- Each persisted run represents the most recent calculated month from that calculation.
- `snapshot_data` stores:
  - `latest_month_summary`
  - `csv_text`
  - `report_text`
- Added a run-history dashboard above the input tables.
- The dashboard scopes history to the selected facility and dataset/scenario.
- Dashboard history groups by `snapshot_month` and shows only the latest successful run for each month.
- Latest Run shows the most recent month with `MP`, `MFP`, `CPP`, `MCC`, `FAA`, and `PRA`.
- Previous Runs shows the prior 12 monthly runs.
- CSV and report downloads are served from `snapshot_data`; MinIO is intentionally not wired.

---

# Files Changed

- `app/streamlit_app.py`
  - Renders the run-history dashboard above input tables.
  - Persists a run snapshot after a successful calculation.

- `app/components/results.py`
  - Added `build_run_snapshot_data()` to create the stored snapshot payload.

- `app/components/run_dashboard.py`
  - Added the Streamlit dashboard UI for Latest Run, Previous Runs, and CSV/report downloads.

- `app/db/run_history.py`
  - Added grouped-by-month run-history query that keeps only the latest run per month for dashboard display.

- `app/db/__init__.py`
  - Exported the grouped run-history reader.

- `tests/test_results_snapshot.py`
  - Added tests for snapshot payload creation.

- `tests/test_run_history.py`
  - Added tests for grouped latest-run-per-month behavior.

- `docs/action_items.md`
  - Marked run history and dashboard UI items complete.
  - Left MinIO export/storage as partial.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the implemented no-MinIO dashboard behavior.

- `.codex/docs/features/dataset-scenarios.md`
  - Documented the current `snapshot_data` payload shape.

---

# Summary And Concerns

This implements the run-history dashboard without MinIO. The backend keeps every successful run in `monthly_snapshot`, while the frontend groups by month and displays only the newest successful run for each month. Downloads come from the stored CSV/report text in `snapshot_data`.

Verification completed:

- `python -m py_compile app/streamlit_app.py app/components/results.py app/components/run_dashboard.py app/db/run_history.py app/db/__init__.py tests/test_run_history.py tests/test_results_snapshot.py`
- `python -m unittest discover -s tests` ran 49 tests successfully.
- `Invoke-WebRequest http://localhost:8501` returned HTTP 200 from the running Streamlit server.

Concern:

- Visual browser verification was attempted, but the in-app browser connector failed before opening the app because its sandbox metadata was malformed in this session.
- MinIO upload/download remains intentionally unwired.

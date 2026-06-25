# User Request And Plan

> "We have a few UI/UX polish items to clean up in our Streamlit app. Please provide the code for the following:
> 1. Dynamic Titles: Make the main app title dynamic so it automatically updates based on the active project and scenario name selected by the user.
> 2. Responsiveness: Refactor the main layout so it's responsive. Convert our standard horizontal rows into stacked columns for smaller window sizes so the tables and stats don't get squished.
> 3. Column Guide Update: Add a small line of instructional text at the very top of the 'Column Guide' expander noting: 'You can also hover over the table headers for quick tooltips.'

## Plan

Implement these UI polish items without changing calculation or database behavior.

- Move the main title rendering until after the selected scenario is known.
- Render the title as `{Project Name} - {Scenario} Invoice Calculator`.
- Add responsive CSS that stacks Streamlit horizontal block rows on narrower screens.
- Add the requested instruction line at the top of every `Column Guide` expander.
- Verify touched Python files compile.

---

# Feature Changes

- The main title now reflects the selected facility and scenario.
- Horizontal Streamlit row layouts stack into vertical sections on screens under `900px`.
- Column Guide expanders now start with the requested note: "You can also hover over the table headers for quick tooltips."

---

# Files Changed

- `app/streamlit_app.py`
  - Removed the static title from `main()`.
  - Renders `"{project_name} - {dataset_name} Invoice Calculator"` after the scenario is selected.
  - Added responsive CSS for narrower screens that stacks Streamlit horizontal blocks and reduces main content padding.

- `app/components/db_tables.py`
  - Added the hover-tooltip reminder at the top of the `Column Guide` expander.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented dynamic titles, responsive stacking, and the updated Column Guide behavior.

---

# Summary And Concerns

This update makes the active facility/scenario clearer, improves small-window readability by stacking horizontal layouts, and gives users a clear hint that column headers also have hover help. It does not alter calculations, database queries, persistence, or run-history behavior.

Verification completed:

- `python -m py_compile app/streamlit_app.py app/components/db_tables.py`

Concern:

- The responsive stacking relies on Streamlit's current `data-testid="stHorizontalBlock"` DOM marker. This is still CSS-only and lightweight, but it should be checked after future Streamlit upgrades.

# User Request And Plan

> Let's give er a try !

Context from the ticket clarification:

- “Stats” means only the existing Latest Run dashboard.
- Calculation output should still display.
- Only successful runs should update the dashboard.

## Plan

Refresh the Latest Run dashboard after a successful calculation without adding a second dashboard rendering path.

- Keep the dashboard database-driven.
- After calculation succeeds and `monthly_snapshot` persistence succeeds, store the generated output in `st.session_state`.
- Trigger `st.rerun()` so the top dashboard reloads from the database and shows the new Latest Run.
- On the rerun, display the saved calculation output below the Run button for the matching project/dataset.
- Do not update session output or rerun for failed calculations.
- Verify `app/streamlit_app.py` compiles.

---

# Feature Changes

- Successful calculation runs now refresh the top Latest Run dashboard immediately.
- Calculation output remains visible after the refresh.
- Failed calculations do not update saved run output and do not trigger the dashboard refresh path.

---

# Files Changed

- `app/streamlit_app.py`
  - Added a `LAST_RUN_OUTPUT_KEY` session-state key.
  - Saves calculation output to session state only after `record_calculation_run(...)` succeeds.
  - Calls `st.rerun()` after successful snapshot persistence so the dashboard reloads from the database.
  - Renders saved output below the Run button on the rerun when the selected project/dataset matches.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Documented the successful-run dashboard refresh behavior.

---

# Summary And Concerns

The dashboard remains database-driven: after a successful run is recorded, the app reruns and the Latest Run panel reloads from `monthly_snapshot`. The generated output is preserved through the rerun using session state, so users still see the calculation output below the Run section.

Verification completed:

- `python -m py_compile app/streamlit_app.py`

Concern:

- This stores the last output DataFrame and report text in Streamlit session state. That is appropriate for the current local UI flow, but very large future reports may need a lighter “reload output from snapshot” path.

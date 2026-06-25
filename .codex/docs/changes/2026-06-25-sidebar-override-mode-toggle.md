# Request

"I want to refine the UI for the 'Override Mode' toggle. Please make the following layout adjustments:
1. Move the Toggle: Move the st.toggle (or checkbox) for 'Override Mode' into the left sidebar (st.sidebar), placing it below the Facility and Scenario selectors.
2. Keep the Warning in Main View: Even though the toggle is in the sidebar, I want the yellow warning message (st.warning("Override Mode is on...")) and the 'Override edit reason' text input to remain in the main content area, appearing right above the input tables only when Override Mode is active.
Please show me the updated layout code for the sidebar and the conditional rendering for the main area."

---

## Plan

1. Move the `Override Mode` toggle state from `app/components/db_tables.py` to the sidebar flow in `app/streamlit_app.py`.
2. Pass the selected boolean into `render_database_table_views(...)`.
3. Keep the warning, override editor, and edit reason fields in the main table component so they appear directly above the input tabs/table area.
4. Preserve backend enforcement and audit behavior unchanged.
5. Run focused compile/tests.

---

## Feature Changes

- Moved the `Override Mode` toggle into the left sidebar below the Scenario selector.
- Kept the Override Mode warning, override editor, and edit reason fields in the main input-table area.
- Preserved the existing backend audit and protection behavior.

---

## Files Changed

- `app/streamlit_app.py`
  - Added the sidebar `Override Mode` toggle after a real scenario is selected.
  - Passed the toggle value into `render_database_table_views(...)`.

- `app/components/db_tables.py`
  - Removed the local main-content toggle.
  - Kept conditional warning/editor/reason rendering in the main content area.

- `.codex/docs/features/database-backed-streamlit-runtime.md`
  - Updated the runtime behavior description for the new sidebar toggle placement.

---

## Summary And Concerns

The layout now matches the requested split: the user activates Override Mode in the sidebar, while the main input area still surfaces the warning and audit fields right above the tables.

Verification:

- `.\.venv\Scripts\python.exe -m py_compile app\streamlit_app.py app\components\db_tables.py`
- `.\.venv\Scripts\python.exe -m unittest tests.test_table_editor_normalization`
- Local Streamlit server returned HTTP 200 at `http://localhost:8503`.
